#!/usr/bin/env python3
"""Desktop watcher: poll inbox by file mtime and run handlers when online."""

from __future__ import annotations

import argparse
import json
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge.protocol import (  # noqa: E402
    bridge_root,
    claim_task,
    finish_task,
    list_tasks,
    load_config,
    utc_now,
    write_heartbeat,
)


STOP = False


def _handle_stop(signum: int, frame: Any) -> None:  # noqa: ARG001
    global STOP
    STOP = True


def run_ping(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "pong": True,
        "echo": task.get("payload", {}),
        "handled_at": utc_now(),
    }


def run_command(payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    cmd = payload.get("command")
    if not cmd:
        raise ValueError("payload.command is required")
    cwd = payload.get("cwd") or None
    shell = bool(payload.get("shell", True))
    completed = subprocess.run(
        cmd if shell else list(cmd),
        cwd=cwd,
        shell=shell,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout[-20_000:],
        "stderr": completed.stderr[-20_000:],
    }


def run_deploy_local_prototype(payload: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    handler_cfg = (cfg.get("handlers") or {}).get("deploy_local_prototype") or {}
    command = payload.get("command") or handler_cfg.get("command")
    workdir = payload.get("workdir") or handler_cfg.get("workdir") or None
    timeout = int(payload.get("timeout_sec") or handler_cfg.get("timeout_sec") or 600)

    if not command:
        # Safe default: record intent without executing unknown shell.
        return {
            "mode": "dry_run",
            "message": "No deploy command configured. Set handlers.deploy_local_prototype.command "
            "in config.json or pass payload.command.",
            "requested": {
                "prototype": payload.get("prototype") or payload.get("name"),
                "repo": payload.get("repo"),
                "branch": payload.get("branch"),
                "workdir": workdir,
                "env": payload.get("env") or {},
            },
            "handled_at": utc_now(),
        }

    result = run_command(
        {"command": command, "cwd": workdir, "shell": True},
        timeout=timeout,
    )
    result["mode"] = "executed"
    result["prototype"] = payload.get("prototype") or payload.get("name")
    return result


def dispatch(task: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    t = task["type"]
    payload = task.get("payload") or {}
    if t == "ping":
        return run_ping(task)
    if t == "run_command":
        timeout = int(payload.get("timeout_sec") or 300)
        return run_command(payload, timeout=timeout)
    if t == "deploy_local_prototype":
        return run_deploy_local_prototype(payload, cfg)
    if t == "custom":
        return {"accepted": True, "payload": payload, "handled_at": utc_now()}
    raise ValueError(f"Unsupported task type: {t}")


def process_once(root: Path, worker_id: str, cfg: dict[str, Any]) -> int:
    processed = 0
    for _mtime, path, task in list_tasks(root / "inbox"):
        claimed = claim_task(root, path, worker_id)
        if not claimed:
            continue
        claimed["status"] = "running"
        claimed["updated_at"] = utc_now()
        try:
            result = dispatch(claimed, cfg)
            finish_task(root, claimed, ok=True, result=result)
        except Exception as exc:  # noqa: BLE001
            finish_task(
                root,
                claimed,
                ok=False,
                error=f"{exc}\n{traceback.format_exc()[-4000:]}",
            )
        processed += 1
    return processed


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Desktop bridge watcher (file-date polling)")
    p.add_argument("--bridge-dir", default=None)
    p.add_argument("--worker-id", default=None)
    p.add_argument("--once", action="store_true", help="Process current inbox once and exit")
    p.add_argument("--interval", type=float, default=None, help="Poll interval seconds")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = bridge_root(args.bridge_dir)
    cfg = load_config(root)
    worker_id = args.worker_id or cfg.get("worker_id") or "desktop-main"
    interval = float(args.interval if args.interval is not None else cfg.get("poll_interval_sec", 2))

    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)

    print(f"[bridge] watching {root}/inbox every {interval}s as {worker_id}", flush=True)
    write_heartbeat(root, worker_id, {"role": "watcher"})

    if args.once:
        n = process_once(root, worker_id, cfg)
        write_heartbeat(root, worker_id, {"role": "watcher", "last_batch": n})
        print(f"[bridge] processed {n} task(s)", flush=True)
        return 0

    while not STOP:
        write_heartbeat(root, worker_id, {"role": "watcher"})
        n = process_once(root, worker_id, cfg)
        if n:
            print(f"[bridge] processed {n} task(s) at {utc_now()}", flush=True)
        time.sleep(interval)

    write_heartbeat(root, worker_id, {"role": "watcher", "online": False})
    # Mark offline explicitly
    hb_path = root / "state" / "heartbeat.json"
    if hb_path.exists():
        data = json.loads(hb_path.read_text(encoding="utf-8"))
        data["online"] = False
        data["updated_at"] = utc_now()
        data["updated_at_unix"] = time.time()
        hb_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("[bridge] stopped", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
