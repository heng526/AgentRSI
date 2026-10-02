#!/usr/bin/env python3
"""Safely score saved Robot answers with the existing GLM answer judge.

This entrypoint never generates or embeds answers. It requires a local copy of
the exact GLM tokenizer and a documented provider-side input-overhead bound
before it will make any request. Missing those inputs is a hard HOLD.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mmagent.prompts import prompt_agent_verify_answer_referencing  # noqa: E402


RUN_ID = "qwen33b-glmembed-robot-full-20260929a"
EXPECTED_PROVIDER = "glm"
EXPECTED_MODEL = "glm-5.3-flash"
EXPECTED_HOST = "open.bigmodel.cn"
INPUT_PRICE_PER_M = Decimal("0.8")
OUTPUT_PRICE_PER_M = Decimal("2.8")
DEFAULT_BUDGET_RMB = Decimal("100.00")
DEFAULT_MAX_API_ATTEMPTS = 1270
MODEL_INPUT_CONTEXT_TOKENS = 1_048_576
# The official GLM OpenAI-compatible API documents max_tokens. Keep this at
# the existing judge's 512-token ceiling, including any reasoning tokens.
REQUEST_MAX_TOKENS = 512
MAX_BILLED_OUTPUT_TOKENS = 512


class SafetyHold(RuntimeError):
    """A preflight or runtime condition that must stop scoring."""


@dataclass(frozen=True)
class ScoreItem:
    video_id: str
    question_id: str
    question: str
    ground_truth_answer: str
    raw_answer: str

    @property
    def key(self) -> tuple[str, str]:
        return self.video_id, self.question_id

    @property
    def is_empty(self) -> bool:
        return not self.raw_answer.strip()

    @property
    def prompt(self) -> str:
        return prompt_agent_verify_answer_referencing.format(
            question=self.question,
            ground_truth_answer=self.ground_truth_answer,
            agent_answer=self.raw_answer,
        )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ceil_fen(value: Decimal) -> Decimal:
    """Round upward to a cent to reserve more than token-linear list price."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_CEILING)


def estimate_cost_rmb(input_tokens: int, output_tokens: int) -> Decimal:
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("token counts must be nonnegative")
    token_cost = (
        Decimal(input_tokens) * INPUT_PRICE_PER_M
        + Decimal(output_tokens) * OUTPUT_PRICE_PER_M
    ) / Decimal(1_000_000)
    return ceil_fen(token_cost)


def parse_judge_output(raw_output: str) -> bool | None:
    """Preserve the existing GLM parser: first whole-word yes/no wins."""
    match = re.search(r"\b(yes|no)\b", (raw_output or "").strip().lower())
    if match is None:
        return None
    return match.group(1) == "yes"


def load_items(answers_path: Path, annotations_path: Path) -> list[ScoreItem]:
    rows = [json.loads(line) for line in answers_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    annotations = json.loads(annotations_path.read_text(encoding="utf-8"))
    return build_items(rows, annotations)


def build_items(rows: list[dict[str, Any]], annotations: dict[str, Any]) -> list[ScoreItem]:
    if not isinstance(annotations, dict):
        raise ValueError("robot annotations must be a video_id keyed object")

    labels: dict[tuple[str, str], dict[str, Any]] = {}
    for video_id, video in annotations.items():
        if not isinstance(video, dict) or not isinstance(video.get("qa_list"), list):
            raise ValueError(f"invalid annotation structure for video_id={video_id!r}")
        for qa in video["qa_list"]:
            question_id = qa.get("question_id")
            if question_id is None:
                raise ValueError("annotation row is missing question_id")
            key = (str(video_id), str(question_id))
            if key in labels:
                raise ValueError(f"duplicate annotation key {key!r}")
            labels[key] = qa

    items: list[ScoreItem] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("answer row must be an object")
        video_id = row.get("video_id")
        question_id = row.get("id")
        if video_id is None or question_id is None:
            raise ValueError("answer row is missing video_id or id")
        key = (str(video_id), str(question_id))
        if key in seen:
            raise ValueError(f"duplicate answer key {key!r}")
        seen.add(key)
        qa = labels.get(key)
        if qa is None:
            raise ValueError(f"no annotation matches answer key {key!r}")
        question = row.get("question")
        ground_truth_answer = qa.get("answer")
        raw_answer = row.get("response")
        if not all(isinstance(value, str) for value in (question, ground_truth_answer, raw_answer)):
            raise ValueError(f"invalid text fields for answer key {key!r}")
        if question != qa.get("question"):
            raise ValueError(f"question mismatch for answer key {key!r}")
        items.append(ScoreItem(key[0], key[1], question, ground_truth_answer, raw_answer))
    return items


def load_existing(output_path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    if not output_path.exists():
        return {}
    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return index_existing_records(records)


def index_existing_records(records: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    done: dict[tuple[str, str], dict[str, Any]] = {}
    for line_no, record in enumerate(records, 1):
        key = (str(record.get("video_id")), str(record.get("id")))
        if key in done:
            raise SafetyHold(f"duplicate result key in output at line {line_no}: {key!r}")
        if record.get("run_id") != RUN_ID:
            raise SafetyHold(f"output contains a result from an unexpected run at line {line_no}")
        done[key] = record
    return done


def append_jsonl(output_path: Path, record: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        import os
        os.fsync(handle.fileno())


def local_input_token_count(tokenizer: Any, prompt: str) -> int:
    """Count a full one-user-message chat input with a local chat template."""
    encoded = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize=True,
        add_generation_prompt=True,
    )
    if hasattr(encoded, "input_ids"):
        encoded = encoded.input_ids
    if encoded and isinstance(encoded[0], list):
        if len(encoded) != 1:
            raise SafetyHold("tokenizer returned an unexpected batch size")
        encoded = encoded[0]
    return len(encoded)


def load_tokenizer(tokenizer_dir: Path) -> Any:
    if not (tokenizer_dir / "tokenizer.json").is_file():
        raise SafetyHold("local exact-model tokenizer.json is missing; no API call is allowed")
    try:
        from transformers import AutoTokenizer
        return AutoTokenizer.from_pretrained(
            str(tokenizer_dir), local_files_only=True, trust_remote_code=False
        )
    except Exception as exc:
        raise SafetyHold(f"local GLM tokenizer could not be loaded offline ({type(exc).__name__})") from None


def input_bound_for_item(
    tokenizer: Any,
    item: ScoreItem,
    provider_overhead_tokens: int | None,
    provider_overhead_evidence: str | None,
) -> int:
    if provider_overhead_tokens is None or not provider_overhead_evidence:
        raise SafetyHold(
            "provider-side prompt overhead has no verified token upper bound; no API call is allowed"
        )
    if provider_overhead_tokens < 0:
        raise SafetyHold("provider-overhead token bound must be nonnegative")
    return local_input_token_count(tokenizer, item.prompt) + provider_overhead_tokens


def validate_scope(items: Iterable[ScoreItem], expected_count: int) -> tuple[int, int]:
    materialized = list(items)
    empty_count = sum(item.is_empty for item in materialized)
    answered_count = len(materialized) - empty_count
    if answered_count != expected_count:
        raise SafetyHold(f"expected {expected_count} nonempty answers, found {answered_count}")
    if empty_count != 6 or len(materialized) != 1276:
        raise SafetyHold(
            f"expected 1,276 total rows with six empty answers; found {len(materialized)} rows/{empty_count} empty"
        )
    return answered_count, empty_count


def validate_all_bounds(
    pending_items: list[ScoreItem],
    tokenizer: Any,
    provider_overhead_tokens: int | None,
    provider_overhead_evidence: str | None,
) -> tuple[dict[tuple[str, str], int], Decimal]:
    bounds: dict[tuple[str, str], int] = {}
    total_reserve = Decimal("0.00")
    for item in pending_items:
        if item.is_empty:
            continue
        bound = input_bound_for_item(
            tokenizer, item, provider_overhead_tokens, provider_overhead_evidence
        )
        if bound > MODEL_INPUT_CONTEXT_TOKENS:
            raise SafetyHold(f"input upper bound exceeds model context for key={item.key!r}")
        bounds[item.key] = bound
        total_reserve += estimate_cost_rmb(bound, MAX_BILLED_OUTPUT_TOKENS)
    return bounds, total_reserve


def build_empty_record(item: ScoreItem) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "run_id": RUN_ID,
        "video_id": item.video_id,
        "id": item.question_id,
        "status": "EMPTY_WRONG",
        "correct": False,
        "api_call_attempted": False,
        "raw_answer": item.raw_answer,
        "raw_judge_output": None,
        "provider": EXPECTED_PROVIDER,
        "model_id": EXPECTED_MODEL,
        "created_at": utc_now(),
        "usage": None,
        "api_cost_rmb": "0.00",
        "reserved_cost_rmb": "0.00",
    }


def resolve_settings() -> dict[str, Any]:
    from urllib.parse import urlparse
    from mmagent.utils.chat_api import glm_client, glm_settings
    settings = glm_settings()
    if settings.get("provider") != EXPECTED_PROVIDER:
        raise SafetyHold("configured provider does not match the approved official GLM provider")
    if settings.get("chat_model") != EXPECTED_MODEL:
        raise SafetyHold("configured model does not match the approved GLM-5.3-Flash model")
    parsed = urlparse(str(settings.get("base_url", "")))
    if parsed.hostname != EXPECTED_HOST or parsed.path.rstrip("/") != "/api/paas/v4":
        raise SafetyHold("configured API host does not match the verified official GLM endpoint")
    # The OpenAI SDK retries selected transient errors by default; this task
    # explicitly permits one attempt per row, so disable its transport retries.
    return {"settings": settings, "client": glm_client().with_options(max_retries=0)}


def extract_usage(response: Any) -> tuple[int, int, dict[str, Any]]:
    usage = getattr(response, "usage", None)
    if usage is None:
        raise SafetyHold("GLM response has no usage object; stop without retry")
    prompt_tokens = getattr(usage, "prompt_tokens", None)
    completion_tokens = getattr(usage, "completion_tokens", None)
    if not isinstance(prompt_tokens, int) or not isinstance(completion_tokens, int):
        raise SafetyHold("GLM response usage is missing integer prompt/completion counts")
    if hasattr(usage, "model_dump"):
        usage_dict = usage.model_dump(mode="json")
    else:
        usage_dict = {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}
    return prompt_tokens, completion_tokens, usage_dict


def response_content(response: Any) -> tuple[str, str | None, str | None]:
    try:
        choice = response.choices[0]
        message = choice.message
        content = message.content or ""
        reasoning = getattr(message, "reasoning_content", None)
        finish_reason = getattr(choice, "finish_reason", None)
    except Exception:
        raise SafetyHold("GLM response shape was invalid; stop without retry") from None
    return content, reasoning, finish_reason


def make_result_record(
    item: ScoreItem,
    *,
    attempt_number: int,
    status: str,
    raw_judge_output: str | None,
    raw_judge_reasoning: str | None,
    correct: bool | None,
    usage: dict[str, Any] | None,
    input_tokens: int | None,
    output_tokens: int | None,
    reserved_cost: Decimal,
    api_cost: Decimal | None,
    finish_reason: str | None,
    response_model: str | None = None,
    error_type: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "run_id": RUN_ID,
        "video_id": item.video_id,
        "id": item.question_id,
        "status": status,
        "judgement_status": "UNJUDGED" if status == "HOLD" else "JUDGED",
        "correct": correct,
        "api_call_attempted": True,
        "attempt_number": attempt_number,
        "raw_answer": item.raw_answer,
        "raw_judge_output": raw_judge_output,
        "raw_judge_reasoning": raw_judge_reasoning,
        "provider": EXPECTED_PROVIDER,
        "model_id": response_model or EXPECTED_MODEL,
        "created_at": utc_now(),
        "usage": usage,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "finish_reason": finish_reason,
        "reserved_cost_rmb": f"{reserved_cost:.2f}",
        "api_cost_rmb": f"{api_cost:.2f}" if api_cost is not None else None,
        "error_type": error_type,
    }


def run(args: argparse.Namespace) -> int:
    answers_path = Path(args.answers).resolve()
    annotations_path = Path(args.annotations).resolve()
    output_path = Path(args.output).resolve()
    if answers_path.parent.name != RUN_ID:
        raise SafetyHold(f"answers path must point to the approved existing run directory {RUN_ID}")
    if args.budget_rmb <= 0 or args.budget_rmb > DEFAULT_BUDGET_RMB:
        raise SafetyHold("budget must be positive and cannot exceed the approved 100 RMB cap")
    items = load_items(answers_path, annotations_path)
    answered_count, empty_count = validate_scope(items, DEFAULT_MAX_API_ATTEMPTS)
    existing = load_existing(output_path)
    unexpected = set(existing) - {item.key for item in items}
    if unexpected:
        raise SafetyHold(f"output contains keys outside the approved run ({len(unexpected)} rows)")
    if any(record.get("status") == "HOLD" for record in existing.values()):
        raise SafetyHold("output already contains a HOLD row; no retry or continuation is allowed")

    pending = [item for item in items if item.key not in existing]
    blank_pending = [item for item in pending if item.is_empty]
    answered_pending = [item for item in pending if not item.is_empty]
    prior_attempts = sum(bool(record.get("api_call_attempted")) for record in existing.values())
    if prior_attempts + len(answered_pending) > DEFAULT_MAX_API_ATTEMPTS:
        raise SafetyHold("resumed run would exceed the authorized API-attempt limit")
    if not args.tokenizer_dir:
        raise SafetyHold("--tokenizer-dir is required; no network tokenizer download is allowed")
    tokenizer = load_tokenizer(Path(args.tokenizer_dir).resolve())

    bounds, pending_reserve = validate_all_bounds(
        answered_pending,
        tokenizer,
        args.provider_overhead_tokens,
        args.provider_overhead_evidence,
    )
    prior_cost = Decimal("0.00")
    for record in existing.values():
        cost = record.get("api_cost_rmb")
        if cost is None:
            cost = record.get("reserved_cost_rmb", "0.00")
        prior_cost += Decimal(str(cost))
    if prior_cost + pending_reserve > args.budget_rmb:
        raise SafetyHold(
            f"preflight spend+reserve {prior_cost + pending_reserve:.2f} RMB exceeds budget {args.budget_rmb:.2f} RMB"
        )

    if not args.execute:
        print(
            f"OFFLINE PREFLIGHT PASS; answered={answered_count}, empty={empty_count}, "
            f"pending_API_attempts={len(answered_pending)}, "
            f"input_and_output_reserve={pending_reserve:.2f} RMB; no API call made"
        )
        return 0

    # No API call occurs before all rows, token bounds, and the full batch reserve pass.
    for item in blank_pending:
        append_jsonl(output_path, build_empty_record(item))
        existing[item.key] = {"status": "EMPTY_WRONG", "api_call_attempted": False, "api_cost_rmb": "0.00"}

    if not answered_pending:
        print(f"No pending GLM rows; answered={answered_count}, empty={empty_count}, attempts={prior_attempts}")
        return 0

    configured = resolve_settings()
    settings = configured["settings"]
    client = configured["client"]
    actual_spend = prior_cost
    api_attempts = prior_attempts
    pending_reserve_remaining = pending_reserve
    for item in answered_pending:
        input_bound = bounds[item.key]
        row_reserve = estimate_cost_rmb(input_bound, MAX_BILLED_OUTPUT_TOKENS)
        if actual_spend + pending_reserve_remaining > args.budget_rmb:
            raise SafetyHold("spend+reserve would exceed the approved cap before the next API call")
        api_attempts += 1
        try:
            response = client.chat.completions.create(
                model=settings["chat_model"],
                messages=[{"role": "user", "content": item.prompt}],
                temperature=0,
                max_tokens=REQUEST_MAX_TOKENS,
                timeout=60,
            )
        except Exception as exc:
            # A failed request may still be billable: consume its complete reservation.
            record = make_result_record(
                item,
                attempt_number=api_attempts,
                status="HOLD",
                raw_judge_output=None,
                raw_judge_reasoning=None,
                correct=None,
                usage=None,
                input_tokens=None,
                output_tokens=None,
                reserved_cost=row_reserve,
                api_cost=None,
                finish_reason=None,
                response_model=None,
                error_type=type(exc).__name__,
            )
            append_jsonl(output_path, record)
            raise SafetyHold("GLM request failed; row held and execution stopped without retry") from None

        raw_output = None
        raw_reasoning = None
        finish_reason = None
        input_tokens = None
        output_tokens = None
        usage_dict = None
        try:
            raw_output, raw_reasoning, finish_reason = response_content(response)
            input_tokens, output_tokens, usage_dict = extract_usage(response)
        except SafetyHold as exc:
            record = make_result_record(
                item,
                attempt_number=api_attempts,
                status="HOLD",
                raw_judge_output=raw_output,
                raw_judge_reasoning=raw_reasoning,
                correct=None,
                usage=usage_dict,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                reserved_cost=row_reserve,
                api_cost=None,
                finish_reason=None,
                response_model=None,
                error_type=str(exc),
            )
            append_jsonl(output_path, record)
            raise

        api_cost = estimate_cost_rmb(input_tokens, output_tokens)
        pending_reserve_remaining -= row_reserve
        actual_spend += api_cost
        parser_result = parse_judge_output(raw_output)
        hold_reason = None
        if input_tokens > input_bound:
            hold_reason = "reported prompt tokens exceeded the pre-call input bound"
        elif output_tokens > MAX_BILLED_OUTPUT_TOKENS:
            hold_reason = "reported completion tokens exceeded the output reserve"
        elif finish_reason == "length":
            hold_reason = "judge response was length-truncated"
        elif parser_result is None:
            hold_reason = "judge output did not contain a parseable yes/no"
        status = "HOLD" if hold_reason else "SCORED"
        record = make_result_record(
            item,
            attempt_number=api_attempts,
            status=status,
            raw_judge_output=raw_output,
            raw_judge_reasoning=raw_reasoning,
            correct=parser_result if status == "SCORED" else None,
            usage=usage_dict,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            reserved_cost=row_reserve,
            api_cost=api_cost,
            finish_reason=finish_reason,
            response_model=getattr(response, "model", None),
            error_type=hold_reason,
        )
        append_jsonl(output_path, record)
        if status == "HOLD":
            raise SafetyHold(f"row held after API response: {hold_reason}; execution stopped")
        if actual_spend + pending_reserve_remaining > args.budget_rmb:
            raise SafetyHold("post-response actual spend plus remaining reserve exceeds the approved cap")

    print(
        f"Scoring complete; answered={answered_count}, empty={empty_count}, "
        f"API attempts={api_attempts}, spend={actual_spend:.2f} RMB"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answers", required=True, help="existing run answers.jsonl")
    parser.add_argument("--annotations", required=True, help="robot.json annotation source")
    parser.add_argument("--output", required=True, help="append-only judge result JSONL")
    parser.add_argument("--tokenizer-dir", help="local exact-model tokenizer directory; never downloaded")
    parser.add_argument("--provider-overhead-tokens", type=int, help="verified max provider-added input tokens")
    parser.add_argument("--provider-overhead-evidence", help="source proving the provider overhead bound")
    parser.add_argument("--budget-rmb", type=Decimal, default=DEFAULT_BUDGET_RMB)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="make real API calls after full preflight; omitted by default",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return run(args)
    except SafetyHold as exc:
        print(f"HOLD: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
