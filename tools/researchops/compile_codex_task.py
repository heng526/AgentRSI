#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Compile a ResearchOps TASK record into a bounded Codex prompt")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--output")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    task_path = Path(args.task)
    if not task_path.is_absolute():
        task_path = repo / task_path
    task = load(task_path)
    state = load(repo / "researchops/state/STATE.json")
    cfg = load(repo / "researchops/config.json")
    p = task.get("payload") or {}

    def bullets(items):
        return "\n".join(f"- {x}" for x in (items or [])) or "- None"

    text = f"""# Codex ResearchOps Task\n\nTask ID: `{task.get('task_id')}`\nRecord ID: `{task.get('record_id')}`\nProject: `{cfg.get('project_id')}`\nAuthorization: `{p.get('authorization_level')}`\nInput state version: `{task.get('input_state_version')}`\nCurrent state version: `{state.get('state_version')}`\nIdempotency key: `{p.get('idempotency_key')}`\n\n## Mandatory source order\n1. `researchops/state/STATE.json`\n2. `{cfg.get('index_path')}`\n3. `{task_path.relative_to(repo).as_posix()}`\n4. current handoff/runtime/evidence referenced by the task\n5. current branch/commit and actual local/server process state\n\n## Mission\n{p.get('mission','')}\n\n## Scientific question\n{p.get('scientific_question','')}\n\n## AUTHORIZED NOW\n{bullets(p.get('authorized_now'))}\n\n## AUTHORIZED ONLY IF\n{bullets(p.get('authorized_only_if'))}\n\n## HARD PROHIBITIONS\n{bullets(p.get('hard_prohibitions'))}\n\n## Required tests\n{bullets(p.get('required_tests'))}\n\n## Required preflight\n{bullets(p.get('required_preflight'))}\n\n## Required outputs\n{bullets(p.get('required_outputs'))}\n\n## Stop conditions\n{bullets(p.get('stop_conditions'))}\n\n## Result contract\nAppend an immutable result record under `researchops/outbox/codex/`. Do not edit STATE, LEDGER, or INDEX directly. If the task is stale in a way that changes scientific semantics, HOLD before L3/L4 execution. Check the idempotency key before execution.\n"""
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
