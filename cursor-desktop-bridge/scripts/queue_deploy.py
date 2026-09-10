#!/usr/bin/env python3
"""Agent helper: create deploy_local_prototype task from Cursor chat."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge.enqueue import main as enqueue_main  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Queue local prototype deploy for desktop app")
    p.add_argument("--bridge-dir", default=None)
    p.add_argument("--name", required=True, help="Prototype name")
    p.add_argument("--repo", default=None)
    p.add_argument("--branch", default="main")
    p.add_argument("--workdir", default=None)
    p.add_argument("--command", default=None, help="Override desktop deploy command")
    p.add_argument("--env", default="{}", help="JSON env map")
    p.add_argument("--priority", type=int, default=7)
    p.add_argument("--allow-offline-queue", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    payload = {
        "prototype": args.name,
        "repo": args.repo,
        "branch": args.branch,
        "workdir": args.workdir,
        "command": args.command,
        "env": json.loads(args.env),
    }
    enqueue_argv = [
        "--type",
        "deploy_local_prototype",
        "--payload",
        json.dumps(payload, ensure_ascii=False),
        "--priority",
        str(args.priority),
        "--source",
        "cursor_chat",
    ]
    if args.bridge_dir:
        enqueue_argv.extend(["--bridge-dir", args.bridge_dir])
    if args.allow_offline_queue:
        enqueue_argv.append("--allow-offline-queue")
    if args.json:
        enqueue_argv.append("--json")
    return enqueue_main(enqueue_argv)


if __name__ == "__main__":
    raise SystemExit(main())
