from __future__ import annotations

import sys
import unittest
from argparse import Namespace
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import score_saved_answers as scorer  # noqa: E402


REVISIT_KEY = ("living_room_06", "living_room_06_Q16")


def make_items():
    items = []
    for i in range(1276):
        if i < 6:
            video_id, qid, answer = f"empty_v{i}", f"empty_q{i}", ""
        elif i == 21:
            video_id, qid, answer = *REVISIT_KEY, "saved answer"
        else:
            video_id, qid, answer = f"v{i}", f"q{i}", "saved answer"
        items.append(scorer.ScoreItem(video_id, qid, f"question {i}", f"truth {i}", answer))
    return items


def make_prior_records(items):
    records = []
    for item in items[:6]:
        records.append({
            "run_id": scorer.RUN_ID,
            "video_id": item.video_id,
            "id": item.question_id,
            "status": "EMPTY_WRONG",
            "api_call_attempted": False,
            "api_cost_rmb": "0.00",
            "reserved_cost_rmb": "0.00",
        })
    prior_valid_items = [item for item in items[6:21]]
    for n, item in enumerate(prior_valid_items, 1):
        records.append({
            "run_id": scorer.RUN_ID,
            "video_id": item.video_id,
            "id": item.question_id,
            "status": "SCORED",
            "correct": True,
            "api_call_attempted": True,
            "attempt_number": n,
            "api_cost_rmb": "0.01",
            "reserved_cost_rmb": "1.21",
        })
    revisit = next(item for item in items if item.key == REVISIT_KEY)
    records.append({
        "run_id": scorer.RUN_ID,
        "video_id": revisit.video_id,
        "id": revisit.question_id,
        "status": "HOLD",
        "correct": None,
        "api_call_attempted": True,
        "attempt_number": 16,
        "api_cost_rmb": "0.01",
        "reserved_cost_rmb": "1.21",
        "request_max_tokens": 512,
    })
    return records


def successful_response(content="Yes", *, prompt_tokens=100, completion_tokens=20, finish_reason="stop"):
    return SimpleNamespace(
        model=scorer.EXPECTED_MODEL,
        choices=[SimpleNamespace(
            message=SimpleNamespace(content=content, reasoning_content=None),
            finish_reason=finish_reason,
        )],
        usage=SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
    )


class ScoreSavedAnswersTests(unittest.TestCase):
    def test_parser_matches_first_whole_word_semantics(self):
        self.assertIs(scorer.parse_judge_output("YES, correct"), True)
        self.assertIs(scorer.parse_judge_output("No."), False)
        self.assertIsNone(scorer.parse_judge_output("yesterday"))
        self.assertIsNone(scorer.parse_judge_output("unclear"))

    def test_exact_prompt_template_is_used(self):
        item = scorer.ScoreItem("v", "q", "question", "truth", "answer")
        self.assertEqual(
            item.prompt,
            scorer.prompt_agent_verify_answer_referencing.format(
                question="question", ground_truth_answer="truth", agent_answer="answer"
            ),
        )

    def test_source_pairing_and_null_empty_response_retention(self):
        rows = [
            {"video_id": "v1", "id": "q1", "question": "Q1", "response": "A1"},
            {"video_id": "v1", "id": "q2", "question": "Q2", "response": None},
        ]
        annotations = {"v1": {"qa_list": [
            {"question_id": "q1", "question": "Q1", "answer": "T1"},
            {"question_id": "q2", "question": "Q2", "answer": "T2"},
        ]}}
        items = scorer.build_items(rows, annotations)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].ground_truth_answer, "T1")
        self.assertEqual(items[1].raw_answer, "")
        self.assertTrue(items[1].is_empty)
        self.assertTrue(scorer.ScoreItem("v1", "q3", "Q3", "T3", "  ").is_empty)

    def test_source_duplicate_pair_is_rejected(self):
        row = {"video_id": "v1", "id": "q1", "question": "Q1", "response": "A1"}
        annotations = {"v1": {"qa_list": [{"question_id": "q1", "question": "Q1", "answer": "T1"}]}}
        with self.assertRaisesRegex(ValueError, "duplicate answer key"):
            scorer.build_items([row, row], annotations)

    def test_fixed_scope_has_1270_nonempty_and_six_empty_rows(self):
        items = make_items()
        self.assertEqual(scorer.validate_scope(items, 1270), (1270, 6))
        self.assertEqual(sum(not item.is_empty for item in items), 1270)

    def test_each_call_reserves_full_official_context_and_128k_output(self):
        self.assertEqual(scorer.REQUEST_MAX_TOKENS, 4096)
        self.assertEqual(scorer.MAX_BILLED_OUTPUT_TOKENS, 131072)
        self.assertEqual(scorer.max_single_request_reserve(), Decimal("1.21"))
        self.assertEqual(scorer.DEFAULT_MAX_ADDITIONAL_API_ATTEMPTS, 1255)
        self.assertEqual(scorer.DEFAULT_MAX_API_ATTEMPTS, 1271)

    def test_costs_round_up_per_request_to_a_cent(self):
        self.assertEqual(scorer.estimate_cost_rmb(1000, 1000), Decimal("0.01"))
        self.assertEqual(scorer.estimate_cost_rmb(0, 512), Decimal("0.01"))
        with self.assertRaises(ValueError):
            scorer.estimate_cost_rmb(-1, 0)

    def test_output_records_are_append_only_and_resume_dedupes(self):
        record = {"run_id": scorer.RUN_ID, "video_id": "v1", "id": "q1", "status": "SCORED"}
        loaded = scorer.index_existing_records([record])
        self.assertIn(("v1", "q1"), loaded)
        with self.assertRaisesRegex(scorer.SafetyHold, "duplicate result key"):
            scorer.index_existing_records([record, record])

    def make_args(self, max_new_api_attempts=1, budget="100.00"):
        return Namespace(
            answers=str(Path("runs") / scorer.RUN_ID / "answers.jsonl"),
            annotations="robot.json",
            prior_results="prior.jsonl",
            output="followup.jsonl",
            budget_rmb=Decimal(budget),
            max_new_api_attempts=max_new_api_attempts,
            execute=True,
        )

    def run_with_mocks(self, items, prior, followup, completion, args=None):
        calls = []
        appended = []

        class MockCompletions:
            def create(self, **kwargs):
                calls.append(kwargs)
                return completion(kwargs) if callable(completion) else completion

        client = SimpleNamespace(chat=SimpleNamespace(completions=MockCompletions()))
        settings = {"chat_model": scorer.EXPECTED_MODEL, "provider": scorer.EXPECTED_PROVIDER}
        args = args or self.make_args()

        def records_for(path):
            return prior if path.name == "prior.jsonl" else followup

        with patch.object(scorer, "load_items", return_value=items), \
             patch.object(scorer, "load_records", side_effect=records_for), \
             patch.object(scorer, "resolve_settings", return_value={"settings": settings, "client": client}), \
             patch.object(scorer, "append_jsonl", side_effect=lambda _path, record: appended.append(record)), \
             patch("builtins.print"):
            result = scorer.run(args)
        return result, calls, appended

    def test_full_followup_regrades_q16_once_then_scores_remaining_without_repeating_prior15(self):
        items = make_items()
        prior = make_prior_records(items)
        result, calls, appended = self.run_with_mocks(items, prior, [], successful_response(), self.make_args(None))
        self.assertEqual(result, 0)
        self.assertEqual(len(calls), 1255)
        self.assertEqual(calls[0]["max_tokens"], 4096)
        self.assertEqual(calls[0]["messages"][0]["content"], next(i for i in items if i.key == REVISIT_KEY).prompt)
        self.assertEqual(appended[0]["key_attempt_number"], 2)
        self.assertEqual(appended[0]["attempt_number"], 17)
        self.assertEqual(appended[0]["scoring_config_version"], scorer.SCORING_CONFIG_VERSION)
        self.assertEqual(appended[0]["request_max_tokens"], 4096)
        self.assertEqual(appended[-1]["attempt_number"], 1271)
        self.assertTrue(all(call["max_tokens"] == 4096 and call["temperature"] == 0 for call in calls))
        self.assertEqual(sum(record["status"] == "SCORED" for record in appended), 1255)
        self.assertEqual(prior[-1]["status"], "HOLD")
        self.assertEqual(prior[-1]["request_max_tokens"], 512)

    def test_single_regrade_checkpoint_targets_only_q16_and_records_new_config(self):
        items = make_items()
        prior = make_prior_records(items)
        result, calls, appended = self.run_with_mocks(items, prior, [], successful_response("No"))
        self.assertEqual(result, 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["max_tokens"], 4096)
        self.assertEqual((appended[0]["video_id"], appended[0]["id"]), REVISIT_KEY)
        self.assertEqual(appended[0]["correct"], False)
        self.assertEqual(appended[0]["key_attempt_number"], 2)

    def test_resume_skips_completed_regrade_and_starts_first_new_key(self):
        items = make_items()
        prior = make_prior_records(items)
        revisit = next(i for i in items if i.key == REVISIT_KEY)
        completed_regrade = {
            "run_id": scorer.RUN_ID, "video_id": revisit.video_id, "id": revisit.question_id,
            "status": "SCORED", "correct": False, "api_call_attempted": True,
            "attempt_number": 17, "key_attempt_number": 2,
            "request_max_tokens": 4096, "scoring_config_version": scorer.SCORING_CONFIG_VERSION,
            "api_cost_rmb": "0.01", "reserved_cost_rmb": "1.21",
        }
        result, calls, appended = self.run_with_mocks(items, prior, [completed_regrade], successful_response())
        self.assertEqual(result, 0)
        self.assertEqual(len(calls), 1)
        self.assertNotEqual((appended[0]["video_id"], appended[0]["id"]), REVISIT_KEY)
        self.assertEqual(appended[0]["attempt_number"], 18)
        self.assertEqual(appended[0]["key_attempt_number"], 1)

    def test_budget_guard_blocks_before_next_call_when_prior_estimate_plus_reserve_exceeds_cap(self):
        items = make_items()
        prior = make_prior_records(items)
        for record in prior:
            if record.get("api_call_attempted"):
                record["api_cost_rmb"] = "0.00"
        prior[6]["api_cost_rmb"] = "98.80"
        calls = []
        args = self.make_args()
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: calls.append(kw))))
        with patch.object(scorer, "load_items", return_value=items), \
             patch.object(scorer, "load_records", side_effect=lambda p: prior if p.name == "prior.jsonl" else []), \
             patch.object(scorer, "resolve_settings", return_value={"settings": {"chat_model": scorer.EXPECTED_MODEL, "provider": scorer.EXPECTED_PROVIDER}, "client": client}):
            with self.assertRaisesRegex(scorer.SafetyHold, "next-request worst-case reserve"):
                scorer.run(args)
        self.assertEqual(calls, [])

    def test_api_error_is_written_as_hold_and_stops_without_retry(self):
        items = make_items()
        prior = make_prior_records(items)
        calls, appended = [], []

        class MockCompletions:
            def create(self, **kwargs):
                calls.append(kwargs)
                raise TimeoutError("simulated offline failure")

        client = SimpleNamespace(chat=SimpleNamespace(completions=MockCompletions()))
        settings = {"chat_model": scorer.EXPECTED_MODEL, "provider": scorer.EXPECTED_PROVIDER}
        args = self.make_args()
        with patch.object(scorer, "load_items", return_value=items), \
             patch.object(scorer, "load_records", side_effect=lambda p: prior if p.name == "prior.jsonl" else []), \
             patch.object(scorer, "resolve_settings", return_value={"settings": settings, "client": client}), \
             patch.object(scorer, "append_jsonl", side_effect=lambda _path, record: appended.append(record)):
            with self.assertRaisesRegex(scorer.SafetyHold, "failed; row held"):
                scorer.run(args)
        self.assertEqual(len(calls), 1)
        self.assertEqual(appended[0]["status"], "HOLD")
        self.assertEqual(appended[0]["reserved_cost_rmb"], "1.21")
        self.assertEqual(appended[0]["key_attempt_number"], 2)

    def test_truncation_at_4096_stops_without_retry_and_preserves_unjudged(self):
        items = make_items()
        prior = make_prior_records(items)
        calls, appended = [], []

        class MockCompletions:
            def create(self, **kwargs):
                calls.append(kwargs)
                return successful_response("", prompt_tokens=300, completion_tokens=4096, finish_reason="length")

        client = SimpleNamespace(chat=SimpleNamespace(completions=MockCompletions()))
        settings = {"chat_model": scorer.EXPECTED_MODEL, "provider": scorer.EXPECTED_PROVIDER}
        with patch.object(scorer, "load_items", return_value=items), \
             patch.object(scorer, "load_records", side_effect=lambda p: prior if p.name == "prior.jsonl" else []), \
             patch.object(scorer, "resolve_settings", return_value={"settings": settings, "client": client}), \
             patch.object(scorer, "append_jsonl", side_effect=lambda _path, record: appended.append(record)):
            with self.assertRaisesRegex(scorer.SafetyHold, "length-truncated"):
                scorer.run(self.make_args(None))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["max_tokens"], 4096)
        self.assertEqual(appended[0]["status"], "HOLD")
        self.assertIsNone(appended[0]["correct"])

    def test_missing_usage_is_held_at_full_reserve_without_retry(self):
        items = make_items()
        prior = make_prior_records(items)
        response = successful_response()
        response.usage = None
        appended, calls = [], []

        class MockCompletions:
            def create(self, **kwargs):
                calls.append(kwargs)
                return response

        client = SimpleNamespace(chat=SimpleNamespace(completions=MockCompletions()))
        with patch.object(scorer, "load_items", return_value=items), \
             patch.object(scorer, "load_records", side_effect=lambda p: prior if p.name == "prior.jsonl" else []), \
             patch.object(scorer, "resolve_settings", return_value={"settings": {"chat_model": scorer.EXPECTED_MODEL, "provider": scorer.EXPECTED_PROVIDER}, "client": client}), \
             patch.object(scorer, "append_jsonl", side_effect=lambda _path, record: appended.append(record)):
            with self.assertRaisesRegex(scorer.SafetyHold, "no usage object"):
                scorer.run(self.make_args())
        self.assertEqual(len(calls), 1)
        self.assertEqual(appended[0]["reserved_cost_rmb"], "1.21")
        self.assertIsNone(appended[0]["api_cost_rmb"])

    def test_unparseable_judge_output_is_held_and_stops(self):
        items = make_items()
        prior = make_prior_records(items)
        calls, appended = [], []

        class MockCompletions:
            def create(self, **kwargs):
                calls.append(kwargs)
                return successful_response("unclear")

        client = SimpleNamespace(chat=SimpleNamespace(completions=MockCompletions()))
        with patch.object(scorer, "load_items", return_value=items), \
             patch.object(scorer, "load_records", side_effect=lambda p: prior if p.name == "prior.jsonl" else []), \
             patch.object(scorer, "resolve_settings", return_value={"settings": {"chat_model": scorer.EXPECTED_MODEL, "provider": scorer.EXPECTED_PROVIDER}, "client": client}), \
             patch.object(scorer, "append_jsonl", side_effect=lambda _path, record: appended.append(record)):
            with self.assertRaisesRegex(scorer.SafetyHold, "parseable yes/no"):
                scorer.run(self.make_args())
        self.assertEqual(len(calls), 1)
        self.assertEqual(appended[0]["status"], "HOLD")


if __name__ == "__main__":
    unittest.main()
