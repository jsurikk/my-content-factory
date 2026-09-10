#!/usr/bin/env python3
"""Minimal self-check for file-date queue."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="bridge-test-") as tmp:
        bridge = Path(tmp)
        for name in ("inbox", "processing", "outbox", "archive", "state"):
            (bridge / name).mkdir()
        (bridge / "config.json").write_text(
            json.dumps(
                {
                    "poll_interval_sec": 1,
                    "heartbeat_max_age_sec": 30,
                    "worker_id": "test-worker",
                    "handlers": {"deploy_local_prototype": {"command": "", "timeout_sec": 30}},
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        # Start watcher briefly via --once after enqueue, but first enqueue offline-allowed
        enq = run(
            [
                sys.executable,
                str(ROOT / "scripts" / "queue_deploy.py"),
                "--bridge-dir",
                str(bridge),
                "--name",
                "demo",
                "--allow-offline-queue",
                "--json",
            ],
            cwd=ROOT,
        )
        assert enq.returncode == 0, enq.stderr + enq.stdout
        data = json.loads(enq.stdout)
        task_id = data["task"]["id"]
        inbox_files = list((bridge / "inbox").glob("task_*.json"))
        assert len(inbox_files) == 1, inbox_files
        mtime_before = inbox_files[0].stat().st_mtime
        time.sleep(0.05)
        # Touch to simulate "exchange by file date"
        inbox_files[0].touch()
        assert inbox_files[0].stat().st_mtime >= mtime_before

        watch = run(
            [
                sys.executable,
                str(ROOT / "bridge" / "watcher.py"),
                "--bridge-dir",
                str(bridge),
                "--once",
            ],
            cwd=ROOT,
        )
        assert watch.returncode == 0, watch.stderr + watch.stdout

        out = bridge / "outbox" / f"{task_id}.json"
        assert out.exists(), list((bridge / "outbox").iterdir())
        result = json.loads(out.read_text(encoding="utf-8"))
        assert result["status"] == "succeeded", result
        assert result["result"]["mode"] == "dry_run", result

        st = run(
            [sys.executable, str(ROOT / "bridge" / "status.py"), "--bridge-dir", str(bridge), "--json"],
            cwd=ROOT,
        )
        assert st.returncode == 0, st.stderr
        status = json.loads(st.stdout)
        assert status["desktop_online"] is True
        assert any(x["id"] == task_id for x in status["folders"]["outbox"])

        # ping
        ping = run(
            [
                sys.executable,
                str(ROOT / "bridge" / "enqueue.py"),
                "--bridge-dir",
                str(bridge),
                "--type",
                "ping",
                "--payload",
                '{"ok":true}',
                "--json",
            ],
            cwd=ROOT,
        )
        assert ping.returncode == 0, ping.stderr + ping.stdout
        watch2 = run(
            [sys.executable, str(ROOT / "bridge" / "watcher.py"), "--bridge-dir", str(bridge), "--once"],
            cwd=ROOT,
        )
        assert watch2.returncode == 0, watch2.stderr
        print("OK", json.dumps({"task_id": task_id, "outbox": result["result"]}, ensure_ascii=False))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
