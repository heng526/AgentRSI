# Node01 read-only audit evidence

- Audit execution: `01a0fbde-9ada-70bd-9da5-29b3cdedd037` (turn `01a0fbde-a833-7529-aedd-4d7fdabcd2e0`); SSH succeeded. Scope was existing files and process listings only; no remote writes or scientific actions.
- ResearchOps control: `CVPR-RSI-NODE01-READ-20261002`; registered after execution start, then finalized from the returned audit.

## Located project roots

- M3: `/home/hust/projects/WXM/rsi/m3-agent-repro`
- Recuris: `/home/hust/research_recuris/Recuris`
- Frozen artifacts: `/home/hust/research_recuris/frozen`

## Existing Robot retrieval and generation artifacts

| Run | Model / embedding | QA / videos | Answered | Unanswered | Scored |
|---|---:|---:|---:|---:|
| `qwen33b-glmembed-robot-full-20260929a` | Qwen3-32B / GLM embedding-3 | 1,276 / 100 | 1,270 | 6 | 0 |
| `bigmodel-glm53flash-robot-full-20260929a` | GLM-5.3-Flash / GLM embedding-3 | 1,276 / 100 | 1,115 | 161 | 0 |

For each run, locate `runs/<run-id>/report.md` and `runs/<run-id>/answers.jsonl` under the M3 root. Both exited 0; no duplicate IDs, unknown IDs, or error lines were found. Unanswered items were in round 5. Explicit evaluation did not run; these counts are not accuracy.

Related provenance notes: 920 videos / 3,214 QA web annotations exist without a Web run. The artifacts include 100 original images and 100 GLM images; there is no separate hash manifest for GLM images. The artifact manifest pins the data snapshot and original image source. Reported source commit `0e3e419…` had a dirty working tree, so the exact executed source tree is not frozen.

## Recuris and SkillFlow evidence

- Recuris tau-squared comparison, source root `/home/hust/research_recuris/Recuris`: train41 M0 0/4 vs candidate 3/4; dev6 M0 4/4 vs candidate 3/4 (candidate minus M0: -25 percentage points on dev). Candidate decision: REJECT; retain M0.
- Split files differ only by line ending: Git copy 316 bytes (SHA prefix `586bae77…`), server copy 317 bytes (`f17ccc5f…`). Normalized bytes and semantics match: train41 / dev6 / test empty.
- SkillFlow has 34 raw trial files per arm and zero exceptions: 32/34 vs 33/34, reported CI [-5.88, +11.76] percentage points. GLM-5.3-Flash was adapted to QwenCode 0.24.6 / Harbor 0.20.0. Its published memory is not this project's evolved policy.

## Runtime and remaining scientific evidence gap

- No matching M3/Recuris working directory or tmux session was found; the old PID was stopped. Other Python processes occupied eight GPUs at 98–100%; they were outside this project's scope and were not investigated. Do not infer that the server was idle.
- Graphs are written during preprocessing. QA control retrieves and writes answer traces; no per-question persistent repair/writeback or repair record affecting later questions was found.
- Evidence supports existing retrieval and generation, but no scoring. The core persistent-repair-to-later-question effect remains unverified. No scientific gate or metric result is asserted here.

This checklist indexes existing evidence only. Raw result files, datasets, credentials, and model artifacts were not copied into the repository.
