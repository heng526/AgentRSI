#!/usr/bin/env python3
"""Write the single combined run report beside the per-question JSONL."""
import argparse
import json
import platform
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from importlib import metadata
from pathlib import Path


def package_version(name):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not installed"


def command_output(command):
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"unavailable ({type(exc).__name__})"


def load_expected(path):
    source = json.loads(path.read_text(encoding="utf-8"))
    expected = {}
    for item in source.values():
        for qa in item["qa_list"]:
            expected[qa["question_id"]] = qa.get("type", [])
    return expected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("robot", "web", "robot-smoke", "web-smoke"), required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--mode", choices=("local-inference", "local-generation-only", "glm-embedding-inference", "glm-control-inference", "glm-evaluation", "azure-evaluation"), required=True)
    parser.add_argument("--exit-code", type=int, default=0)
    parser.add_argument("--started-epoch", type=float, default=time.time())
    parser.add_argument("--log-file", type=Path)
    parser.add_argument("--max-qas", type=int)
    args = parser.parse_args()

    expected = load_expected(args.annotations)
    rows = []
    if args.results.is_file():
        with args.results.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise SystemExit(f"Invalid JSONL at line {line_number}: {exc}")

    ids = [row.get("id") for row in rows]
    duplicates = [key for key, count in Counter(ids).items() if count > 1]
    observed = set(ids)
    unexpected = sorted(str(key) for key in observed - set(expected))
    smoke = args.max_qas is not None
    missing = [] if smoke else sorted(set(expected) - observed)
    target_count = min(args.max_qas, len(expected)) if smoke else len(expected)
    known_rows = [row for row in rows if row.get("id") in expected]
    answered = [row for row in known_rows if row.get("status") == "answered" and row.get("response")]
    unanswered = [row for row in known_rows if row not in answered]
    scored = [row for row in known_rows if isinstance(row.get("judge_result", row.get("gpt_eval")), bool)]
    correct = sum(row.get("judge_result", row.get("gpt_eval")) for row in scored)
    judge_models = sorted({str(row.get("judge_model", "unknown")) for row in scored})
    judge_backends = sorted({str(row.get("judge_provider", "unknown")) for row in scored})
    retrieval_skipped = sum(row.get("retrieval_mode") == "skipped" for row in known_rows)
    embedding_backends = sorted({str(row.get("embedding_provider", "unknown")) for row in known_rows})
    embedding_models = sorted({str(row.get("embedding_model", "unknown")) for row in known_rows})
    control_models = sorted({str(row.get("control_model", "unknown")) for row in known_rows})
    control_backends = sorted({str(row.get("control_api_provider", row.get("control_provider", "unknown"))) for row in known_rows})

    by_type = defaultdict(lambda: [0, 0])
    for row in known_rows:
        for label in expected[row["id"]]:
            by_type[label][0] += int(bool(row.get("response")))
            by_type[label][1] += 1

    started = time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(args.started_epoch))
    finished_epoch = time.time()
    duration = max(0.0, finished_epoch - args.started_epoch)
    git_commit = command_output(["git", "rev-parse", "HEAD"])
    cuda_summary = "unavailable"
    try:
        import torch
        visible = torch.cuda.device_count()
        pairs = []
        if visible >= 2:
            pairs = [
                f"0→1={torch.cuda.can_device_access_peer(0, 1)}",
                f"1→0={torch.cuda.can_device_access_peer(1, 0)}",
            ]
        cuda_summary = f"available={torch.cuda.is_available()}, visible={visible}, CUDA={torch.version.cuda}, P2P={'/'.join(pairs) or 'n/a'}"
    except Exception as exc:
        cuda_summary = f"unavailable ({type(exc).__name__})"

    log_tail = []
    notable = []
    if args.log_file and args.log_file.is_file():
        log_lines = args.log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        log_tail = log_lines[-45:]
        notable = [line for line in log_lines if re.search(r"ERROR|WARNING|Traceback|out of memory|NCCL.*(error|fail)", line, re.I)][-30:]

    lines = [
        f"# M3-Agent run report: {args.run_id}",
        "",
        "## Run",
        "",
        f"- Dataset: `{args.split}`",
        f"- Mode: `{args.mode}`",
        f"- Start: {started}",
        f"- Duration: {duration / 60:.1f} minutes",
        f"- Process exit code: {args.exit_code}",
        f"- Source commit: `{git_commit}`",
        f"- Python: {platform.python_version()}; PyTorch: {package_version('torch')}; Transformers: {package_version('transformers')}; vLLM: {package_version('vllm')}",
        f"- CUDA/GPU/P2P: {cuda_summary}",
        "",
        "## Inference results",
        "",
        f"- QA rows: {len(rows)} / expected {target_count}",
        f"- Answered: {len(answered)}; unanswered: {len(unanswered)}",
        f"- Duplicate IDs: {len(duplicates)}; unknown IDs: {len(unexpected)}",
        f"- Retrieval skipped: {retrieval_skipped} / {len(known_rows)} QA records",
        f"- Embedding backend: {', '.join(embedding_backends)}; model: {', '.join(embedding_models)}",
        f"- Control backend: {', '.join(control_backends)}; model: {', '.join(control_models)}",
        f"- Missing IDs: {len(missing)}" if not smoke else "- Missing-ID check: not applicable to a smoke subset",
        f"- Search rounds: min={min((int(row.get('rounds', 0)) for row in known_rows), default=0)}, max={max((int(row.get('rounds', 0)) for row in known_rows), default=0)}",
    ]
    if scored:
        accuracy = 100 * correct / len(scored)
        lines.extend([
            f"- Judge coverage: {len(scored)} / {len(known_rows)}; backend: {', '.join(judge_backends)}; model: {', '.join(judge_models)}",
            f"- Judge accuracy: {accuracy:.2f}% (denominator: scored rows only)",
        ])
    else:
        lines.append("- Evaluation: NOT RUN; no accuracy is reported")
    lines.extend(["", "## Answer completion by question type", ""])
    for label, (count, total) in sorted(by_type.items()):
        lines.append(f"- {label}: {count}/{total} answered")
    if missing:
        lines.extend(["", "## Missing QA IDs", "", ", ".join(missing[:100])])
        if len(missing) > 100:
            lines.append(f"… and {len(missing) - 100} more")
    if duplicates or unexpected or unanswered:
        lines.extend(["", "## Anomalies", ""])
        if duplicates:
            lines.append(f"- Duplicate IDs: {', '.join(str(value) for value in duplicates[:50])}")
        if unexpected:
            lines.append(f"- IDs absent from annotations: {', '.join(unexpected[:50])}")
        if unanswered:
            lines.append(f"- Unanswered IDs: {', '.join(str(row.get('id')) for row in unanswered[:50])}")
    if notable:
        lines.extend(["", "## Warnings and errors", ""])
        lines.extend(f"- `{line[-500:]}`" for line in notable)
    if log_tail:
        lines.extend(["", "## Final run output", "", "```text"])
        lines.extend(log_tail)
        lines.append("```")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    temp_report = args.report.with_name(args.report.name + ".tmp")
    temp_report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temp_report.replace(args.report)

    integrity_errors = []
    if len(rows) != target_count:
        integrity_errors.append(f"expected {target_count} rows, got {len(rows)}")
    if duplicates:
        integrity_errors.append(f"{len(duplicates)} duplicate QA IDs")
    if unexpected:
        integrity_errors.append(f"{len(unexpected)} unknown QA IDs")
    if not smoke and missing:
        integrity_errors.append(f"{len(missing)} QA IDs missing")
    if unanswered:
        integrity_errors.append(f"{len(unanswered)} QA records have no final answer")
    if args.exit_code != 0:
        integrity_errors.append(f"inference exited with code {args.exit_code}")
    if integrity_errors:
        raise SystemExit("Run needs attention; see report: " + "; ".join(integrity_errors))
    print(f"Report written: {args.report}")


if __name__ == "__main__":
    main()
