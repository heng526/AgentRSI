#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path

LEVELS = {"L0_READ": 0, "L1_ENGINEERING": 1, "L2_PREFLIGHT": 2, "L3_SCIENTIFIC_RUN": 3, "L4_PROTOCOL_CHANGE": 4}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Select the next pending Codex task allowed for an automation level")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--max-authorization", default="L2_PREFLIGHT", choices=LEVELS)
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    state = load(repo / "researchops/state/STATE.json")
    max_level = LEVELS[args.max_authorization]
    tasks = state.get("tasks") or {}
    candidates = []
    for task_path in sorted((repo / "researchops/outbox/gpt").glob("TASK-*.json")):
        rec = load(task_path)
        tid = rec.get("task_id")
        if not tid or tasks.get(tid, {}).get("status") != "PENDING":
            continue
        level_name = (rec.get("payload") or {}).get("authorization_level", "L4_PROTOCOL_CHANGE")
        if LEVELS.get(level_name, 99) > max_level:
            continue
        candidates.append((rec.get("created_at") or "", rec.get("record_id") or "", task_path, rec))
    if not candidates:
        print("NO_ELIGIBLE_TASK")
        return 3
    candidates.sort(key=lambda x: (x[0], x[1]))
    _, _, path, rec = candidates[0]
    print(path.relative_to(repo).as_posix())
    print(rec.get("task_id"))
    print((rec.get("payload") or {}).get("authorization_level"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
