#!/usr/bin/env python3
"""Show bridge status: online heartbeat, inbox/outbox by file date."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge.protocol import (  # noqa: E402
    bridge_root,
    is_desktop_online,
    list_tasks,
    load_config,
    read_heartbeat,
)


def fmt_mtime(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--bridge-dir", default=None)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    root = bridge_root(args.bridge_dir)
    cfg = load_config(root)
    max_age = float(cfg.get("heartbeat_max_age_sec", 30))
    online = is_desktop_online(root, max_age_sec=max_age)
    hb = read_heartbeat(root)

    folders = {}
    for name in ("inbox", "processing", "outbox", "archive"):
        items = [
            {
                "id": task["id"],
                "type": task["type"],
                "status": task["status"],
                "mtime": fmt_mtime(mtime),
                "mtime_unix": mtime,
                "priority": task.get("priority", 5),
                "path": str(path),
            }
            for mtime, path, task in list_tasks(root / name)
        ]
        folders[name] = items

    payload = {
        "bridge_dir": str(root),
        "desktop_online": online,
        "heartbeat": hb,
        "folders": folders,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"bridge: {root}")
        print(f"desktop: {'ONLINE' if online else 'OFFLINE'}")
        if hb:
            print(f"heartbeat: {hb.get('updated_at')} worker={hb.get('worker_id')}")
        for name, items in folders.items():
            print(f"{name}: {len(items)}")
            for item in items[:10]:
                print(f"  - {item['id']} [{item['status']}] mtime={item['mtime']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
