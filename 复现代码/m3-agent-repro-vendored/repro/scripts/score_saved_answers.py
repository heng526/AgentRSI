#!/usr/bin/env python3
"""Safely score saved Robot answers with the existing GLM answer judge.

This entrypoint never generates or embeds answers. Before each request it
reserves the official model's full input-context and maximum-output cost. It
stops when cumulative spend plus the next request reserve would exceed budget.
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
DEFAULT_MAX_API_ATTEMPTS = 1271
DEFAULT_MAX_ADDITIONAL_API_ATTEMPTS = 1255
MODEL_INPUT_CONTEXT_TOKENS = 1_048_576
MODEL_MAX_OUTPUT_TOKENS = 131_072
# Follow-up config: the prior 512-token attempt and HOLD remain in the prior
# result file; this config rejudges that single key once and scores new keys.
REQUEST_MAX_TOKENS = 4096
SCORING_CONFIG_VERSION = "official-glm-5.3-flash-max-tokens-4096-followup"
MAX_BILLED_OUTPUT_TOKENS = MODEL_MAX_OUTPUT_TOKENS


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
        if not isinstance(question, str) or not isinstance(ground_truth_answer, str):
            raise ValueError(f"invalid text fields for answer key {key!r}")
        if raw_answer is None:
            raw_answer = ""
        elif not isinstance(raw_answer, str):
            raise ValueError(f"invalid response field for answer key {key!r}")
        if question != qa.get("question"):
            raise ValueError(f"question mismatch for answer key {key!r}")
        items.append(ScoreItem(key[0], key[1], question, ground_truth_answer, raw_answer))
    return items


def load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_existing(output_path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    return index_existing_records(load_records(output_path))


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


def max_single_request_reserve() -> Decimal:
    """Conservatively reserve official maximum context and output for one call."""
    return estimate_cost_rmb(MODEL_INPUT_CONTEXT_TOKENS, MAX_BILLED_OUTPUT_TOKENS)


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
    key_attempt_number: int,
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
        "key_attempt_number": key_attempt_number,
        "scoring_config_version": SCORING_CONFIG_VERSION,
        "request_max_tokens": REQUEST_MAX_TOKENS,
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
    prior_results_path = Path(args.prior_results).resolve()
    if output_path == prior_results_path:
        raise SafetyHold("follow-up output must be separate so the original 512-token records remain immutable")
    if answers_path.parent.name != RUN_ID:
        raise SafetyHold(f"answers path must point to the approved existing run directory {RUN_ID}")
    if args.budget_rmb <= 0 or args.budget_rmb > DEFAULT_BUDGET_RMB:
        raise SafetyHold("budget must be positive and cannot exceed the approved 100 RMB cap")
    items = load_items(answers_path, annotations_path)
    answered_count, empty_count = validate_scope(items, 1270)
    prior_records = load_records(prior_results_path)
    prior = index_existing_records(prior_records)
    followup_records = load_records(output_path)
    followup = index_existing_records(followup_records)
    valid_keys = {item.key for item in items}
    if (set(prior) | set(followup)) - valid_keys:
        raise SafetyHold("prior/follow-up output contains keys outside the approved run")

    regrade_key = ("living_room_06", "living_room_06_Q16")
    prior_attempts_records = [r for r in prior_records if r.get("api_call_attempted")]
    prior_scored = {key for key, record in prior.items() if record.get("status") == "SCORED"}
    prior_empty = {key for key, record in prior.items() if record.get("status") == "EMPTY_WRONG"}
    prior_holds = {key for key, record in prior.items() if record.get("status") == "HOLD"}
    if len(prior_attempts_records) != 16 or len(prior_scored) != 15 or prior_holds != {regrade_key}:
        raise SafetyHold("prior result file does not match the approved 15-score/one-Q16-HOLD history")
    if len(prior_empty) != 6:
        raise SafetyHold("prior result file does not contain the six verified empty-answer records")
    if any(record.get("status") == "HOLD" for record in followup.values()):
        raise SafetyHold("follow-up already has a HOLD row; stop with no retry or continuation")
    if set(followup) & (prior_scored | prior_empty):
        raise SafetyHold("follow-up attempts to duplicate a prior valid judgment or empty-answer record")
    if any(key != regrade_key for key in set(followup) & prior_holds):
        raise SafetyHold("only the specifically authorized Q16 HOLD may be re-evaluated")

    if args.max_new_api_attempts is not None and args.max_new_api_attempts <= 0:
        raise SafetyHold("--max-new-api-attempts must be positive")
    completed_followup = {key for key, record in followup.items() if record.get("status") == "SCORED"}
    for key, record in followup.items():
        if record.get("status") != "SCORED" or record.get("request_max_tokens") != REQUEST_MAX_TOKENS:
            raise SafetyHold("follow-up result does not match the approved 4096-token configuration")

    by_key = {item.key: item for item in items}
    candidates: list[ScoreItem] = []
    if regrade_key not in completed_followup:
        candidates.append(by_key[regrade_key])
    for item in items:
        if item.is_empty or item.key in prior_scored or item.key in prior_empty:
            continue
        if item.key == regrade_key or item.key in completed_followup:
            continue
        candidates.append(item)
    if len(candidates) > DEFAULT_MAX_ADDITIONAL_API_ATTEMPTS:
        raise SafetyHold("follow-up would exceed the approved 1,255 additional-attempt limit")

    all_records = prior_records + followup_records
    prior_attempts = sum(bool(record.get("api_call_attempted")) for record in all_records)
    if prior_attempts + len(candidates) > DEFAULT_MAX_API_ATTEMPTS:
        raise SafetyHold("follow-up would exceed the approved 1,271 total API-attempt limit")
    prior_cost = Decimal("0.00")
    for record in all_records:
        cost = record.get("api_cost_rmb")
        if cost is None:
            cost = record.get("reserved_cost_rmb", "0.00")
        prior_cost += Decimal(str(cost))
    row_reserve = max_single_request_reserve()
    if candidates and prior_cost + row_reserve > args.budget_rmb:
        raise SafetyHold(
            f"current spend plus next-request worst-case reserve {prior_cost + row_reserve:.2f} RMB "
            f"exceeds budget {args.budget_rmb:.2f} RMB"
        )

    if not args.execute:
        print(
            f"OFFLINE PREFLIGHT PASS; prior_attempts={len(prior_attempts_records)}, "
            f"prior_valid={len(prior_scored)}, followup_done={len(completed_followup)}, "
            f"pending_API_attempts={len(candidates)}, next_request_reserve={row_reserve:.2f} RMB, "
            f"conservative_spend={prior_cost:.2f} RMB; no API call made"
        )
        return 0

    if not candidates:
        print(f"No follow-up rows pending; total_attempts={prior_attempts}, conservative_spend={prior_cost:.2f} RMB")
        return 0

    configured = resolve_settings()
    settings = configured["settings"]
    client = configured["client"]
    actual_spend = prior_cost
    api_attempts = prior_attempts
    items_to_process = candidates
    if args.max_new_api_attempts is not None:
        items_to_process = candidates[:args.max_new_api_attempts]
    for index, item in enumerate(items_to_process):
        if actual_spend + row_reserve > args.budget_rmb:
            raise SafetyHold(
                f"current spend plus next-request worst-case reserve {actual_spend + row_reserve:.2f} RMB "
                f"would exceed budget {args.budget_rmb:.2f} RMB; remaining answers are UNJUDGED"
            )
        api_attempts += 1
        key_attempt_number = 1 + sum(
            1 for record in all_records
            if record.get("api_call_attempted")
            and (str(record.get("video_id")), str(record.get("id"))) == item.key
        )
        max_key_attempts = 2 if item.key == regrade_key else 1
        if key_attempt_number > max_key_attempts:
            raise SafetyHold(f"per-answer attempt limit exceeded for key={item.key!r}")
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
                key_attempt_number=key_attempt_number,
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
                key_attempt_number=key_attempt_number,
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
        actual_spend += api_cost
        parser_result = parse_judge_output(raw_output)
        hold_reason = None
        if input_tokens > MODEL_INPUT_CONTEXT_TOKENS:
            hold_reason = "reported prompt tokens exceeded the official model context ceiling"
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
            key_attempt_number=key_attempt_number,
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
        print(
            f"attempt={api_attempts}/{DEFAULT_MAX_API_ATTEMPTS} key_attempt={key_attempt_number} "
            f"key={item.video_id}/{item.question_id} status={status} "
            f"usage={input_tokens}/{output_tokens} cost_est={api_cost:.2f} "
            f"conservative_total={actual_spend:.2f} reserve={row_reserve:.2f}",
            flush=True,
        )
        if status == "HOLD":
            raise SafetyHold(f"row held after API response: {hold_reason}; execution stopped")
        if index + 1 < len(items_to_process) and actual_spend + row_reserve > args.budget_rmb:
            raise SafetyHold(
                f"cumulative actual spend plus next-request worst-case reserve "
                f"{actual_spend + row_reserve:.2f} RMB exceeds the approved cap; remaining answers are UNJUDGED"
            )

    remaining = len(candidates) - len(items_to_process)
    state = "Scoring complete" if remaining == 0 else "Scoring checkpoint"
    print(
        f"{state}; eligible_nonempty={answered_count}, empty={empty_count}, "
        f"new_attempts={len(items_to_process)}, total_attempts={api_attempts}, "
        f"conservative_spend={actual_spend:.2f} RMB, remaining_unjudged={remaining}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answers", required=True, help="existing run answers.jsonl")
    parser.add_argument("--annotations", required=True, help="robot.json annotation source")
    parser.add_argument("--prior-results", required=True, help="immutable prior 512-token score file")
    parser.add_argument("--output", required=True, help="append-only judge result JSONL")
    parser.add_argument("--budget-rmb", type=Decimal, default=DEFAULT_BUDGET_RMB)
    parser.add_argument(
        "--max-new-api-attempts",
        type=int,
        help="optional checkpoint limit for this invocation; existing results are skipped",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="make real API calls after prior-history and per-request budget checks; omitted by default",
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
