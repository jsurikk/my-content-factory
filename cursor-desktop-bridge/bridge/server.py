#!/usr/bin/env python3
"""Optional HTTP API for cloud/paid hosting or LAN access.

Endpoints:
  GET  /health
  GET  /status
  POST /tasks                 enqueue
  GET  /tasks/{id}            find in folders
  POST /heartbeat             desktop marks itself online
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge.protocol import (  # noqa: E402
    bridge_root,
    create_task,
    enqueue_task,
    ensure_dirs,
    is_desktop_online,
    list_tasks,
    load_config,
    load_json,
    read_heartbeat,
    task_path,
    write_heartbeat,
)


def create_app(root: Path, token: str | None):
    try:
        from fastapi import FastAPI, Header, HTTPException
        from pydantic import BaseModel, Field
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "Install optional deps: pip install fastapi uvicorn\n" + str(exc)
        ) from exc

    app = FastAPI(title="Cursor Desktop Bridge", version="0.1.0")
    cfg = load_config(root)
    max_age = float(cfg.get("heartbeat_max_age_sec", 30))

    class EnqueueBody(BaseModel):
        type: str = Field(..., examples=["deploy_local_prototype"])
        payload: dict[str, Any] = Field(default_factory=dict)
        source: str = "api"
        priority: int = 5
        require_online: bool = True
        allow_offline_queue: bool = True
        id: str | None = None

    class HeartbeatBody(BaseModel):
        worker_id: str = "desktop-main"
        extra: dict[str, Any] = Field(default_factory=dict)

    def check_auth(authorization: str | None) -> None:
        if not token:
            return
        expected = f"Bearer {token}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"ok": True, "desktop_online": is_desktop_online(root, max_age)}

    @app.get("/status")
    def status(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        check_auth(authorization)
        folders = {
            name: [
                {"id": t["id"], "status": t["status"], "type": t["type"], "mtime_unix": m}
                for m, _p, t in list_tasks(root / name)
            ]
            for name in ("inbox", "processing", "outbox", "archive")
        }
        return {
            "bridge_dir": str(root),
            "desktop_online": is_desktop_online(root, max_age),
            "heartbeat": read_heartbeat(root),
            "folders": folders,
        }

    @app.post("/tasks")
    def enqueue(body: EnqueueBody, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        check_auth(authorization)
        online = is_desktop_online(root, max_age)
        if body.require_online and not online and not body.allow_offline_queue:
            raise HTTPException(status_code=503, detail="desktop_offline")
        task = create_task(
            task_type=body.type,
            payload=body.payload,
            source=body.source,
            priority=body.priority,
            requires_online=body.require_online,
            task_id=body.id,
        )
        if not online:
            task["status"] = "offline_pending"
        path = enqueue_task(root, task)
        return {"ok": True, "task": task, "path": str(path), "desktop_online": online}

    @app.get("/tasks/{task_id}")
    def get_task(task_id: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        check_auth(authorization)
        dirs = ensure_dirs(root)
        for name in ("outbox", "processing", "inbox", "archive"):
            path = task_path(dirs[name], task_id)
            if path.exists():
                return {"folder": name, "task": load_json(path)}
        raise HTTPException(status_code=404, detail="not_found")

    @app.post("/heartbeat")
    def heartbeat(body: HeartbeatBody, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        check_auth(authorization)
        path = write_heartbeat(root, body.worker_id, body.extra)
        return {"ok": True, "path": str(path)}

    return app


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="HTTP API for Cursor Desktop Bridge")
    p.add_argument("--bridge-dir", default=None)
    p.add_argument("--host", default=None)
    p.add_argument("--port", type=int, default=None)
    p.add_argument("--token", default=None, help="Bearer token (or BRIDGE_API_TOKEN)")
    args = p.parse_args(argv)

    root = bridge_root(args.bridge_dir)
    cfg = load_config(root)
    http_cfg = cfg.get("http") or {}
    host = args.host or http_cfg.get("host") or "127.0.0.1"
    port = int(args.port or http_cfg.get("port") or 8787)
    token = args.token or os.environ.get("BRIDGE_API_TOKEN") or http_cfg.get("token")
    if token == "change-me":
        token = os.environ.get("BRIDGE_API_TOKEN")

    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("pip install fastapi uvicorn") from exc

    app = create_app(root, token=token if token and token != "change-me" else None)
    print(f"[bridge-api] http://{host}:{port} root={root}", flush=True)
    uvicorn.run(app, host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
