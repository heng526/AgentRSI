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


class FakeTokenizer:
    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        assert tokenize is True
        assert add_generation_prompt is True
        assert len(messages) == 1 and messages[0]["role"] == "user"
        return list(range(len(messages[0]["content"].encode("utf-8")) + 3))


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

    def test_source_pairing_and_empty_response_retention(self):
        rows = [
            {"video_id": "v1", "id": "q1", "question": "Q1", "response": "A1"},
            {"video_id": "v1", "id": "q2", "question": "Q2", "response": "  "},
        ]
        annotations = {
            "v1": {
                "qa_list": [
                    {"question_id": "q1", "question": "Q1", "answer": "T1"},
                    {"question_id": "q2", "question": "Q2", "answer": "T2"},
                ]
            }
        }
        items = scorer.build_items(rows, annotations)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].ground_truth_answer, "T1")
        self.assertEqual(items[1].raw_answer, "  ")
        self.assertTrue(items[1].is_empty)

    def test_source_duplicate_pair_is_rejected(self):
        row = {"video_id": "v1", "id": "q1", "question": "Q1", "response": "A1"}
        annotations = {"v1": {"qa_list": [{"question_id": "q1", "question": "Q1", "answer": "T1"}]}}
        with self.assertRaisesRegex(ValueError, "duplicate answer key"):
            scorer.build_items([row, row], annotations)

    def test_blank_answers_are_fixed_scope_and_not_api_candidates(self):
        items = [
            scorer.ScoreItem(str(i), str(i), "q", "gt", "" if i < 6 else "answer")
            for i in range(1276)
        ]
        self.assertEqual(scorer.validate_scope(items, 1270), (1270, 6))
        self.assertEqual(sum(not item.is_empty for item in items), 1270)

    def test_token_bound_requires_verified_provider_overhead_before_tokenizing(self):
        item = scorer.ScoreItem("v", "q", "q", "gt", "answer")

        class NoTokenize:
            def apply_chat_template(self, *args, **kwargs):
                raise AssertionError("must fail before tokenization without the overhead proof")

        with self.assertRaisesRegex(scorer.SafetyHold, "provider-side prompt overhead"):
            scorer.input_bound_for_item(NoTokenize(), item, None, None)

    def test_exact_bound_adds_documented_provider_overhead_and_reserves_worst_output(self):
        item = scorer.ScoreItem("v", "q", "q", "gt", "answer")
        bound = scorer.input_bound_for_item(FakeTokenizer(), item, 17, "official provider source")
        self.assertEqual(bound, len(item.prompt.encode("utf-8")) + 3 + 17)
        self.assertEqual(scorer.REQUEST_MAX_COMPLETION_TOKENS, 502)
        self.assertEqual(scorer.MAX_BILLED_OUTPUT_TOKENS, 512)

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

    def test_full_scope_mock_scores_1270_and_never_calls_for_six_empty_rows(self):
        items = [
            scorer.ScoreItem(f"v{i}", f"q{i}", "question", "truth", "" if i < 6 else "answer")
            for i in range(1276)
        ]
        calls = []
        appended = []

        class MockCompletions:
            def create(self, **kwargs):
                calls.append(kwargs)
                return SimpleNamespace(
                    model=scorer.EXPECTED_MODEL,
                    choices=[SimpleNamespace(
                        message=SimpleNamespace(content="Yes", reasoning_content=None),
                        finish_reason="stop",
                    )],
                    usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1),
                )

        client = SimpleNamespace(chat=SimpleNamespace(completions=MockCompletions()))
        settings = {"chat_model": scorer.EXPECTED_MODEL, "provider": scorer.EXPECTED_PROVIDER}
        args = Namespace(
            answers=str(Path("runs") / scorer.RUN_ID / "answers.jsonl"),
            annotations="unused-robot.json",
            output="unused-results.jsonl",
            tokenizer_dir="mock-tokenizer",
            provider_overhead_tokens=0,
            provider_overhead_evidence="mocked verified source",
            expected_nonempty=1270,
            max_api_attempts=1270,
            budget_rmb=Decimal("100.00"),
            execute=True,
        )

        with patch.object(scorer, "load_items", return_value=items), \
             patch.object(scorer, "load_existing", return_value={}), \
             patch.object(scorer, "load_tokenizer", return_value=FakeTokenizer()), \
             patch.object(scorer, "resolve_settings", return_value={"settings": settings, "client": client}), \
             patch.object(scorer, "append_jsonl", side_effect=lambda _path, record: appended.append(record)):
            self.assertEqual(scorer.run(args), 0)

        self.assertEqual(len(calls), 1270)
        self.assertTrue(all("agent_answer: answer" in call["messages"][0]["content"] for call in calls))
        self.assertEqual(len(appended), 1276)
        self.assertEqual(sum(record["status"] == "EMPTY_WRONG" for record in appended), 6)
        self.assertEqual(sum(record["status"] == "SCORED" for record in appended), 1270)
        self.assertTrue(all(call["max_completion_tokens"] == 502 for call in calls))

    def test_mock_api_error_is_written_as_hold_and_stops_without_retry(self):
        items = [
            scorer.ScoreItem(f"v{i}", f"q{i}", "question", "truth", "" if i < 6 else "answer")
            for i in range(1276)
        ]
        calls = []
        appended = []

        class MockCompletions:
            def create(self, **kwargs):
                calls.append(kwargs)
                raise TimeoutError("simulated offline failure")

        client = SimpleNamespace(chat=SimpleNamespace(completions=MockCompletions()))
        settings = {"chat_model": scorer.EXPECTED_MODEL, "provider": scorer.EXPECTED_PROVIDER}
        args = Namespace(
            answers=str(Path("runs") / scorer.RUN_ID / "answers.jsonl"),
            annotations="unused-robot.json",
            output="unused-results.jsonl",
            tokenizer_dir="mock-tokenizer",
            provider_overhead_tokens=0,
            provider_overhead_evidence="mocked verified source",
            expected_nonempty=1270,
            max_api_attempts=1270,
            budget_rmb=Decimal("100.00"),
            execute=True,
        )

        with patch.object(scorer, "load_items", return_value=items), \
             patch.object(scorer, "load_existing", return_value={}), \
             patch.object(scorer, "load_tokenizer", return_value=FakeTokenizer()), \
             patch.object(scorer, "resolve_settings", return_value={"settings": settings, "client": client}), \
             patch.object(scorer, "append_jsonl", side_effect=lambda _path, record: appended.append(record)):
            with self.assertRaisesRegex(scorer.SafetyHold, "failed; row held"):
                scorer.run(args)

        self.assertEqual(len(calls), 1)
        self.assertEqual(sum(record["status"] == "HOLD" for record in appended), 1)


if __name__ == "__main__":
    unittest.main()
