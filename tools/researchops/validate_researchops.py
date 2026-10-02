#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate ResearchOps repository state")
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    required = ["researchops/config.json", "researchops/state/STATE.json", "researchops/ledger/LEDGER.json", "researchops/ledger/LEDGER.md"]
    errors = []
    for rel in required:
        if not (repo / rel).is_file():
            errors.append(f"missing {rel}")
    if errors:
        print("RESEARCHOPS VALIDATION: FAIL")
        for e in errors:
            print(f"- {e}")
        return 1
    cfg = load(repo / "researchops/config.json")
    state = load(repo / "researchops/state/STATE.json")
    ledger = load(repo / "researchops/ledger/LEDGER.json")
    primary_index = repo / cfg["index_path"]
    if not primary_index.is_file():
        errors.append(f"missing primary index {cfg['index_path']}")
    generated_rel = cfg.get("researchops_sidecar_index_path") if cfg.get("index_mode") == "sidecar" else cfg["index_path"]
    if not (repo / generated_rel).is_file():
        errors.append(f"missing reducer index {generated_rel}")
    if state.get("project_id") != cfg.get("project_id"):
        errors.append("STATE project_id mismatch")
    if state.get("reducer_writer") != cfg.get("reducer_writer"):
        errors.append("reducer writer mismatch")
    entries = ledger.get("entries") or []
    seqs = [e.get("seq") for e in entries]
    if seqs != list(range(1, len(entries) + 1)):
        errors.append("ledger sequence is not contiguous from 1")
    if int(state.get("last_seq", 0)) != len(entries):
        errors.append("STATE last_seq does not match ledger length")
    record_ids = [e.get("record_id") for e in entries]
    if len(record_ids) != len(set(record_ids)):
        errors.append("duplicate ledger record_id")
    processed = state.get("processed_records") or {}
    if set(processed) != set(record_ids):
        errors.append("processed_records set differs from ledger records")
    for tid, task in (state.get("tasks") or {}).items():
        if task.get("status") in {"PASS", "RUNNING"} and not task.get("idempotency_key"):
            errors.append(f"task {tid} is {task.get('status')} without idempotency_key")
    if errors:
        print("RESEARCHOPS VALIDATION: HOLD")
        for e in errors:
            print(f"- {e}")
        return 2
    print("RESEARCHOPS VALIDATION: PASS")
    print(f"project={cfg['project_id']} state_version={state.get('state_version')} last_seq={state.get('last_seq')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
