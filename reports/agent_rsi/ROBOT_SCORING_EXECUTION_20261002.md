# Robot saved-answer scoring execution record

## Scope and authorization

This record covers only the existing run `qwen33b-glmembed-robot-full-20260929a`.
The one-shot authorization covers the 1,270 saved nonempty responses, six empty
responses marked wrong without a request, at most one API attempt per answer key,
and a hard RMB 100 ceiling. Reuse the existing answer-referencing prompt,
temperature, and first-whole-word `yes|no` parser. Any API, usage, truncation, or
parse error is `UNJUDGED`/`HOLD`; stop immediately and never retry or count it as
wrong. Do not regenerate answers, embed, train, change the split, labels, metric,
prompt, or judge semantics.

The user later corrected the provider information and confirmed the original
successful setup was the official GLM API (message `Sentinel_d3899488d22481918ac1dbf77467b874`):
`https://open.bigmodel.cn/api/paas/v4`, model `glm-5.3-flash`, with the key held
in node01's `~/.config/m3-agent/bigmodel.env`. This correction changes only the
provider/model/endpoint; all scoring limits and stop conditions above remain.

## Verified configuration and price

- A single read-only audit of node01 confirmed the config file exists with mode
  `600`, host `open.bigmodel.cn`, API path `/api/paas/v4`, chat model
  `glm-5.3-flash`, embedding model `embedding-3`, and a nonempty `GLM_API_KEY`
  field. No credential value was read into output, printed, copied, or changed.
- The archived successful run report records GLM `embedding-3` for embeddings,
  but does not itself record the historical chat endpoint. The exact official
  endpoint/model above are confirmed by the user's direct original-run evidence
  and the matching protected config.
- The current official Zhipu pricing table lists GLM-5.3-Flash at input CNY 0.8 and
  output CNY 2.8 per million tokens. The official model page lists a 1M context
  and 128K maximum output. Sources: [���� API ����](https://docs.bigmodel.cn/cn/guide/start/pricing),
  [GLM-5.3-Flash ģ��˵��](https://docs.bigmodel.cn/cn/guide/models/vlm/glm-5.3-flash).
- ���׵� OpenAI �����ĵ� supports `max_tokens`; the scorer now sends
  `max_tokens=512`, matching the existing judge's output ceiling.
  [OpenAI API �����ĵ�](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction).
- The archive contains 1,276 unique `(video_id, id)` rows: 1,270 nonempty
  responses and six null responses, normalized to empty and wrong without a
  request. All questions and labels pair with the
  saved annotations. Rendered prompts total 1,619,299 UTF-8 bytes, with a
  maximum of 1,815 bytes per nonempty prompt; these byte lengths are not treated
  as a verified token upper bound.

## Scorer and offline verification

`���ִ���/m3-agent-repro-vendored/repro/scripts/score_saved_answers.py` is an
append-only score-only tool for the named run. It uses the existing judge prompt
and parser, checks the official provider/model/endpoint, disables SDK retries,
fsyncs each result, resumes by `(video_id, id)`, and stops at the first API,
usage, truncation, or parse issue. Before each request it reserves the official
full input context (1,048,576 tokens) and maximum output (131,072 tokens), using
the official input/output list prices and rounding up to cents. This is CNY
1.21 per attempt; the next request is sent only if cumulative actual or
conservatively reserved spend plus CNY 1.21 remains within the CNY 100 ceiling.
Unknown usage or a request error consumes that request's full reserve and stops
the run. Unprocessed rows remain unjudged.

After the provider correction, the API routing and documented request parameter
were updated without changing the prompt, temperature, or parser. A null
response value is normalized to empty, matching the six empty rows already
verified in the archive. The scorer's offline mock tests pass **11/11**,
including a per-request budget-boundary case. These mocks generated no GLM API
traffic.

## Execution status: HOLD on first length-truncated judge response

The first formal request scored `living_room_06/living_room_06_Q01`: the judge
returned `No`, recorded as `correct=false`, with 278 input tokens and 433
completion tokens (430 reasoning tokens); cost rounded up to CNY 0.01.

The serial run stopped on attempt 16, `living_room_06/living_room_06_Q16`, when
the official API returned `finish_reason=length`. That row is `HOLD` with
`correct=null`, 319 input tokens, 512 completion tokens (511 reasoning tokens),
and CNY 0.01 actual cost against its CNY 1.21 reserve. It was not retried.

Final persisted status at stop: **16** API attempts, **15** judged rows, **1**
truncated `HOLD`, **6** empty rows marked wrong without calls, and **1,254**
nonempty rows not attempted and therefore unjudged. Aggregate usage for the 16
attempts was 4,569 input tokens and 2,514 completion tokens (2,466 reasoning
tokens). Cumulative rounded actual cost was **CNY 0.16**. No API transport error
occurred. The partial judgments are not reported as accuracy or a scientific
gate result. ResearchOps scientific stage remains `BOOTSTRAP`, and
`scientific_head_sha` remains `null`.

## Follow-up execution addendum: HOLD with 839 rows still unjudged

The separately approved 4096-token follow-up preserves the original 512-token
file unchanged and writes to
`runs/qwen33b-glmembed-robot-full-20260929a/glm_judge_scores_followup_4096.jsonl`.
Every follow-up row records configuration version
`official-glm-5.3-flash-max-tokens-4096-followup`. The re-evaluation of
`living_room_06/living_room_06_Q16` succeeded at global attempt 17: the judge
returned `No` (`correct=false`), with 319 input and 398 completion tokens
(395 reasoning tokens). Its original 512-token `HOLD` remains in the prior
file as history.

The first SSH control stream reset after visible output for attempt 431. A
read-only inspection then confirmed that the remote scorer was no longer
running and the append-only follow-up file had 416 complete `SCORED` rows,
global attempts 17�C432, with no follow-up `HOLD`. An offline resume preflight
passed: 839 additional rows remained, the next-request reserve was CNY 1.21,
and accumulated per-request rounded estimates were CNY 4.32 including the
original batch. The persisted follow-up rows total 119,898 input tokens and
64,556 completion tokens; 144 were judged correct and 272 incorrect. At the
published token rates, their unrounded usage-based list-price estimate is
CNY 0.2766752; the sum of per-call rounded estimates is CNY 4.16. Neither is a
provider invoice, which was not checked.

An attempt to resume the remaining authorized rows was rejected by automatic
approval review because it could not establish trusted user authorization for
sending the saved answers and annotations to the GLM API destination. No
workaround was attempted and no API request was sent after that rejection.
The follow-up therefore remains `HOLD`: 416 follow-up labels are persisted,
839 nonempty rows remain `UNJUDGED`, and the six empty rows remain wrong without
API calls. Across both files there are 432 API attempts and 431 distinct
judged answer keys; the old Q16 hold is superseded only for current scoring by
its successful 4096-token result, but is retained immutably in the prior file.
Because the run is incomplete and uses mixed 512/4096-token configurations,
no aggregate accuracy or scientific-gate result is reported. ResearchOps
remains `BOOTSTRAP` with `scientific_head_sha=null`.
