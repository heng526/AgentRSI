# Robot saved-answer scoring execution record

## Scope and approval

This record covers only the existing run `qwen33b-glmembed-robot-full-20260929a`.
The user selected GLM in message `Sentinel_2f7e76d42284819180a876165ac8f673` and
approved the one-shot RMB 100 ceiling at `2026-10-02T12:32:38Z` in
`Sentinel_90c142b529488191b2782a9ffce647d5`. The preceding proposal
`Sentinel_9b7b7848617081919a4cdcf0d25d1484` documented the 1,270 nonempty answers,
six empty answers, and stop-on-error scope.

Only the 1,270 saved nonempty `response` values may be sent to the judge. The
six empty responses are wrong without a request. The maximum is one real API
attempt per nonempty pair `(video_id, id)`, at most 1,270 attempts. API or parse
errors are `UNJUDGED` and `HOLD`, stop the run, and are never retried or counted
as wrong. The run does not regenerate answers, embed anything, change the split,
metric, prompt, or judge semantics, or perform memory-repair experiments.

## Verified facts

- The original node01 `m3-agent-repro` environment is reachable and was used for
  read-only checks. No model or API call was made.
- The protected config resolves to provider `bailian`, model
  `ZHIPU/GLM-5.3-Flash`, and the Beijing DashScope OpenAI-compatible endpoint.
  No credential value was printed or copied.
- Alibaba's public Beijing price for this model is input CNY 0.8 per million
  tokens and output CNY 2.8 per million tokens, excluding promotions. The model
  page reports a 1,048,576-token input/context limit and 131,072-token maximum
  output: [official GLM-5.3-Flash model page](https://help.aliyun.com/zh/model-studio/glm-5-3-flash-by-zhipu).
- Alibaba documents `max_completion_tokens` for completion limits and notes
  actual output usage can differ by up to 10 tokens. The scorer therefore
  requests 502 and reserves 512 output tokens per attempt:
  [official DashScope API reference](https://help.aliyun.com/en/model-studio/qwen-api-via-dashscope).
- The existing saved run has 1,276 unique `(video_id, id)` rows, 1,270 nonempty
  `response` values, six empty values, and no duplicate keys. All 1,270 scoring
  pairs match the archived annotation labels and questions.
- The exact existing prompt rendered for the 1,270 nonempty rows totals
  1,619,299 UTF-8 bytes; maximum row size is 1,815 bytes. This is a size
  measurement only, not a verified GLM token-count upper bound.

## Engineering and budget guard

`repro/scripts/score_saved_answers.py` is a standalone, append-only scorer. It
reuses `prompt_agent_verify_answer_referencing` and the existing first-whole-word
`yes|no` parser. It locks the named run, provider, model, fixed 1,270-attempt
limit, and RMB 100 maximum. It requires a local exact-model tokenizer plus
evidence for a provider-side input-overhead upper bound before any request. It
calculates all pending per-row reserves before starting, rounds every reserve
up to CNY 0.01, persists each outcome with `fsync`, deduplicates by
`(video_id, id)`, and disables OpenAI SDK retries. It stops on the first API,
usage, truncation, or parse problem.

The offline test suite passed 11/11 tests. One mock test exercised the complete
1,270-row flow with 1,270 in-process fake responses and six no-request empty
rows; a second mock injected a request error and verified exactly one attempt,
an `UNJUDGED`/`HOLD` record, and immediate stop. These were mocks only, not API
attempts.

## Execution status: HOLD before first request

The original environment's Transformers version is 4.51.0. Loading the exact
GLM-5.3-Flash tokenizer in offline-only mode failed because it is not cached.
The Alibaba docs reviewed here do not provide a corresponding token-count
endpoint for this alias. Z.ai's official tokenizer endpoint requires a Z.ai
Bearer token and documents only GLM-4.6, GLM-4.6v, and GLM-4.5, so it is not an
authorized or matching counter for the configured Bailian endpoint:
[Z.ai tokenizer API](https://docs.z.ai/api-reference/tools/tokenizer).

Therefore the measured UTF-8 byte lengths cannot be promoted to a reliable
token upper bound, and no provider-added input overhead ceiling is verified.
The 1,048,576-token absolute model limit would reserve more than the approved
RMB 100 across all 1,270 calls. The scorer correctly remains gated and no real
judge call has been made. Current real API attempts: **0 sent, 0 successful,
0 failed**. No score, accuracy, or scientific gate result exists. ResearchOps
scientific stage remains `BOOTSTRAP`, with `scientific_head_sha=null`.

No L4 protocol-change task was opened; this work uses the existing protocol.
