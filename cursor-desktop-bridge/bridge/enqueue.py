#!/usr/bin/env python3
"""Enqueue a task for the desktop app (used from Cursor chat / CI / scripts)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge.protocol import (  # noqa: E402
    bridge_root,
    create_task,
    enqueue_task,
    is_desktop_online,
    list_tasks,
    load_config,
    read_heartbeat,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Enqueue Cursor→Desktop bridge task")
    p.add_argument("--bridge-dir", default=None, help="Bridge root (or CURSOR_BRIDGE_DIR)")
    p.add_argument(
        "--type",
        required=True,
        choices=["deploy_local_prototype", "run_command", "ping", "custom"],
    )
    p.add_argument("--payload", default="{}", help="JSON object payload")
    p.add_argument("--payload-file", default=None, help="Path to JSON payload file")
    p.add_argument("--source", default="cursor_chat")
    p.add_argument("--priority", type=int, default=5)
    p.add_argument("--require-online", action="store_true", default=True)
    p.add_argument("--allow-offline-queue", action="store_true", help="Queue even if desktop offline")
    p.add_argument("--id", default=None, help="Optional fixed task id")
    p.add_argument("--json", action="store_true", help="Print machine-readable result")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = bridge_root(args.bridge_dir)
    cfg = load_config(root)
    max_age = float(cfg.get("heartbeat_max_age_sec", 30))

    if args.payload_file:
        payload = json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
    else:
        payload = json.loads(args.payload)
    if not isinstance(payload, dict):
        raise SystemExit("payload must be a JSON object")

    online = is_desktop_online(root, max_age_sec=max_age)
    if not online and not args.allow_offline_queue:
        hb = read_heartbeat(root)
        msg = {
            "ok": False,
            "error": "desktop_offline",
            "hint": "Start desktop watcher, or pass --allow-offline-queue",
            "heartbeat": hb,
        }
        print(json.dumps(msg, ensure_ascii=False, indent=2) if args.json else msg["hint"])
        return 2

    task = create_task(
        task_type=args.type,
        payload=payload,
        source=args.source,
        priority=args.priority,
        requires_online=args.require_online,
        task_id=args.id,
    )
    if not online:
        task["status"] = "offline_pending"

    path = enqueue_task(root, task)
    result = {
        "ok": True,
        "task": task,
        "path": str(path),
        "desktop_online": online,
        "inbox_count": len(list_tasks(root / "inbox")),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        state = "online" if online else "offline_pending"
        print(f"Queued {task['id']} ({task['type']}) → {path} [{state}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
