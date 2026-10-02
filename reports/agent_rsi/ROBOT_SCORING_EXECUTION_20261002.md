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
  and 128K maximum output. Sources: [智谱 API 定价](https://docs.bigmodel.cn/cn/guide/start/pricing),
  [GLM-5.3-Flash 模型说明](https://docs.bigmodel.cn/cn/guide/models/vlm/glm-5.3-flash).
- 智谱的 OpenAI 兼容文档 supports `max_tokens`; the scorer now sends
  `max_tokens=512`, matching the existing judge's output ceiling.
  [OpenAI API 兼容文档](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction).
- The archive contains 1,276 unique `(video_id, id)` rows: 1,270 nonempty
  responses and six empty responses. All questions and labels pair with the
  saved annotations. Rendered prompts total 1,619,299 UTF-8 bytes, with a
  maximum of 1,815 bytes per nonempty prompt; these byte lengths are not treated
  as a verified token upper bound.

## Scorer and offline verification

`复现代码/m3-agent-repro-vendored/repro/scripts/score_saved_answers.py` is an
append-only score-only tool for the named run. It uses the existing judge prompt
and parser, checks the official provider/model/endpoint, disables SDK retries,
fsyncs each result, resumes by `(video_id, id)`, and stops at the first API,
usage, truncation, or parse issue. Its full-batch preflight still requires a
local exact-model tokenizer and evidence for any provider-side input-overhead
upper bound before making a request.

After the provider correction, the API routing and documented request parameter
were updated without changing the prompt, temperature, or parser. The scorer's
offline mock tests pass **11/11**. These mocks generated no GLM API traffic.

## Execution status: HOLD before first request

No exact GLM-5.3-Flash tokenizer is cached in the original node01 environment;
offline loading with Transformers 4.51.0 failed. No documented provider-side
input-overhead ceiling has been established. Without those bounds, the 1,270-row
full-batch input reserve cannot be shown to fit the approved budget. The
documented absolute context ceiling alone reserves CNY 0.85 per row when rounded
up to cents, or CNY 1,079.50 for 1,270 requests, before any prior spend; this is
above the CNY 100 cap. Therefore no live request has been made.

Current live scoring attempts: **0 sent, 0 successful, 0 failed**. No score,
accuracy, or scientific gate result exists. ResearchOps scientific stage remains
`BOOTSTRAP`, and `scientific_head_sha` remains `null`.
