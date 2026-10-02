# Robot 全量 GLM 判分与论文证据状态（2026-10-02）

## 已完成的归档 run

归档 run 为 `qwen33b-glmembed-robot-full-20260929a`，原
`report.md` 记录了 Robot 1,276/1,276 题、1,270 条非空回答、6 条空答、无缺失或重复题 ID。推理模式是
`glm-embedding-inference`，使用 GLM `embedding-3` 与本地
`models/M3-Agent-Control`；原运行源码提交为
`0e3e41939bd8a0b66d756e7b7eb8d5fe9992da5c`。原报告标记
`Evaluation: NOT RUN`；本次只对这些已保存回答补做判分。

旧评分文件保留 15 条有效 512-token 判分、Q16 的一条
`finish_reason=length` 历史 `HOLD`，以及 6 条无需 API 的空答记错记录。
4096-token follow-up 文件保留 1,255 条有效判分，其中 Q16 的唯一授权重评判为错。
两个文件只在 Q16 题 ID 上重叠；API attempt 1–1,271 连续，没有其他题重试。
旧文件的 16 条 API 行没有逐行 `request_max_tokens` 或配置版本字段；
其 512-token 来源由当时固定源码和[执行记录](ROBOT_SCORING_EXECUTION_20261002.md)证明。
follow-up 每行均标记 `request_max_tokens=4096` 和配置版本。

按 `(video_id, id)` 合并时，Q16 使用成功的 4096-token 结果；
旧 `HOLD` 只保留作历史，不计成错或未判。核对结果：
1,270 条非空回答全部有最终布尔判分，6 条空答按既有规则为错，
**422/1,276 正确，准确率 33.0721%**（展示为 33.07%）；
错误 854 条，其中 6 条为空答。这个指标仅描述该归档 run 的完整判分。

逐条核对确认：1,276 个源题 ID 唯一；全部题目和参考答案与 Robot
标注一致；评分记录中的原回答与归档回答一致；1,270 条最终判分均与
既有首个完整词 `yes|no` 解析器一致且响应正常结束；
所有 1,271 次 API 记录都有 usage，provider/model 均为
`glm` / `glm-5.3-flash`。follow-up 没有 `HOLD`，未判数为零。

## 错误分布

| 标注类型 | 正确 / 题数 | 正确率 |
|---|---:|---:|
| Cross-Modal Reasoning | 154 / 476 | 32.35% |
| General Knowledge Extraction | 87 / 327 | 26.61% |
| Multi-Detail Reasoning | 287 / 842 | 34.09% |
| Multi-Hop Reasoning | 35 / 85 | 41.18% |
| Person Understanding | 238 / 548 | 43.43% |

728/1,276 题有多个类型标注，因此类型行会重叠，不能相加为总体。
General Knowledge Extraction 是这组描述性分层中正确率最低的标注；
它本身不能证明具体失败机制。

| 场景 | 正确 / 题数 | 正确率 |
|---|---:|---:|
| bedroom | 50 / 152 | 32.89% |
| gym | 22 / 48 | 45.83% |
| kitchen | 106 / 307 | 34.53% |
| living_room | 95 / 309 | 30.74% |
| meeting_room | 17 / 68 | 25.00% |
| office | 31 / 95 | 32.63% |
| study | 101 / 297 | 34.01% |

场景题量与类型构成不同；这些比例只用于定位应人工核查的样本，
不能单独归因为检索、记忆或生成模块。

## 用量、可复用证据与论文边界

1,271 次 API 响应报告 365,919 输入、200,985 输出 token
（其中 196,841 为 reasoning token）。按本次归档单价线性计算的
未取整估价为 **¥0.8554932**；逐请求向上取整到分并用于预算检查的
估算合计 **¥12.71**，低于授权上限 ¥100。每次下一请求按 ¥1.21
最坏情况预留。两种数字均不是已核实的服务商账单。

node01 保留 `answers.jsonl`、原评分 JSONL、follow-up JSONL、
原 `report.md`、Robot 标注和 100 个记忆图文件。
每条归档回答都有检索与生成 trace、`before_clip` 信息；
这些可供逐案核对 848 条非空判错案例。已有
`repro/scripts/score_saved_answers.py` 提供评分与断点续跑，
`repro/scripts/summarize_results.py` 提供推理覆盖/类型汇总，
`visualization.py` 可查看记忆图。
原汇总器只读取回答行内的 `judge_result/gpt_eval`，而此归档回答没有
这两个字段；它不能直接合并两个独立评分文件，也不应直接产出此指标。

下一步论文分析应在完整 1,276 题上，用固定的人工核查准则把错误
区分为证据检索、回答生成、参考答案/判分争议等类别，并复核代表案例。
当前只有这一归档 run 的完整 judge 指标；缺少在同一判分口径下
核对过的比较运行和人工错误归因。**ResearchOps 科学阶段保持
`BOOTSTRAP`，`scientific_head_sha=null`，未宣称科研 gate PASS。**
