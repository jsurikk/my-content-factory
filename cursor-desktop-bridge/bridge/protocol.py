from __future__ import annotations

import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_TYPES = {
    "deploy_local_prototype",
    "run_command",
    "ping",
    "custom",
}

STATUSES = {
    "queued",
    "claimed",
    "running",
    "succeeded",
    "failed",
    "rejected",
    "offline_pending",
}

_SAFE_ID = re.compile(r"^task_[A-Za-z0-9_\-]+$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_task_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"task_{stamp}_{uuid.uuid4().hex[:6]}"


def bridge_root(explicit: str | Path | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("CURSOR_BRIDGE_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def ensure_dirs(root: Path) -> dict[str, Path]:
    dirs = {
        "root": root,
        "inbox": root / "inbox",
        "processing": root / "processing",
        "outbox": root / "outbox",
        "archive": root / "archive",
        "state": root / "state",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def task_path(folder: Path, task_id: str) -> Path:
    if not _SAFE_ID.match(task_id):
        raise ValueError(f"Unsafe task id: {task_id}")
    return folder / f"{task_id}.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Expected object in {path}")
    return data


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def validate_task(task: dict[str, Any]) -> dict[str, Any]:
    for key in ("id", "type", "created_at", "status", "payload"):
        if key not in task:
            raise ValueError(f"Missing required field: {key}")
    if not _SAFE_ID.match(str(task["id"])):
        raise ValueError(f"Invalid task id: {task['id']}")
    if task["type"] not in TASK_TYPES:
        raise ValueError(f"Unknown task type: {task['type']}")
    if task["status"] not in STATUSES:
        raise ValueError(f"Unknown status: {task['status']}")
    if not isinstance(task["payload"], dict):
        raise ValueError("payload must be an object")
    return task


def create_task(
    *,
    task_type: str,
    payload: dict[str, Any] | None = None,
    source: str = "cursor_chat",
    priority: int = 5,
    requires_online: bool = True,
    task_id: str | None = None,
) -> dict[str, Any]:
    now = utc_now()
    task = {
        "id": task_id or new_task_id(),
        "type": task_type,
        "created_at": now,
        "updated_at": now,
        "source": source,
        "priority": max(1, min(10, int(priority))),
        "status": "queued",
        "requires_online": bool(requires_online),
        "payload": payload or {},
        "result": None,
        "error": None,
        "claimed_by": None,
        "claimed_at": None,
    }
    return validate_task(task)


def enqueue_task(root: Path, task: dict[str, Any]) -> Path:
    dirs = ensure_dirs(root)
    task = validate_task(task)
    path = task_path(dirs["inbox"], task["id"])
    if path.exists():
        raise FileExistsError(f"Task already exists: {path}")
    atomic_write_json(path, task)
    return path


def list_tasks(folder: Path) -> list[tuple[float, Path, dict[str, Any]]]:
    items: list[tuple[float, Path, dict[str, Any]]] = []
    if not folder.exists():
        return items
    for path in folder.glob("task_*.json"):
        try:
            mtime = path.stat().st_mtime
            task = validate_task(load_json(path))
            items.append((mtime, path, task))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    # Newest file date first, then higher priority.
    items.sort(key=lambda x: (-x[0], -int(x[2].get("priority", 5))))
    return items


def write_heartbeat(root: Path, worker_id: str, extra: dict[str, Any] | None = None) -> Path:
    dirs = ensure_dirs(root)
    path = dirs["state"] / "heartbeat.json"
    data = {
        "worker_id": worker_id,
        "online": True,
        "updated_at": utc_now(),
        "updated_at_unix": time.time(),
        **(extra or {}),
    }
    atomic_write_json(path, data)
    return path


def read_heartbeat(root: Path) -> dict[str, Any] | None:
    path = ensure_dirs(root)["state"] / "heartbeat.json"
    if not path.exists():
        return None
    try:
        return load_json(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def is_desktop_online(root: Path, max_age_sec: float = 30.0) -> bool:
    hb = read_heartbeat(root)
    if not hb:
        return False
    updated = float(hb.get("updated_at_unix") or 0)
    if updated <= 0:
        return False
    return (time.time() - updated) <= max_age_sec and bool(hb.get("online", True))


def claim_task(root: Path, path: Path, worker_id: str) -> dict[str, Any] | None:
    """Move inbox → processing atomically when possible. Returns claimed task or None."""
    dirs = ensure_dirs(root)
    task = validate_task(load_json(path))
    if task["status"] not in {"queued", "offline_pending"}:
        return None
    dest = task_path(dirs["processing"], task["id"])
    if dest.exists():
        return None
    task["status"] = "claimed"
    task["claimed_by"] = worker_id
    task["claimed_at"] = utc_now()
    task["updated_at"] = utc_now()
    # Write then move: safer across cloud sync folders that dislike rename races.
    atomic_write_json(dest, task)
    try:
        path.unlink(missing_ok=True)
    except OSError:
        # If delete fails (locked sync), leave duplicate and prefer processing copy.
        pass
    return task


def finish_task(
    root: Path,
    task: dict[str, Any],
    *,
    ok: bool,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> Path:
    dirs = ensure_dirs(root)
    task = dict(task)
    task["status"] = "succeeded" if ok else "failed"
    task["result"] = result
    task["error"] = error
    task["updated_at"] = utc_now()
    out = task_path(dirs["outbox"], task["id"])
    atomic_write_json(out, task)
    proc = task_path(dirs["processing"], task["id"])
    archive = task_path(dirs["archive"], task["id"])
    atomic_write_json(archive, task)
    if proc.exists():
        try:
            proc.unlink()
        except OSError:
            pass
    return out

def load_config(root: Path) -> dict[str, Any]:
    for name in ("config.json", "config.example.json"):
        path = root / name
        if path.exists():
            return load_json(path)
    return {}
