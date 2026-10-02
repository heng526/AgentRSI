# Recuris 独立复现记录（2026-09-29）

## Material Passport

- 来源：Recuris 官方仓库 `7d3745ab787b1206ccd981cb1511100476097266`；τ²-Bench 固定提交 `8ebb7499622fc2be9b9d510d6f7a7653461f4f29`。
- 运行位置：node01，`/home/hust/research_recuris/Recuris`；Python 3.12.14，独立虚拟环境；GLM-5.3-Flash 同时作为 Meta-Agent、下游 Agent、模拟用户及断言评分模型。
- 配置性质：GLM 改造复现，**不与论文原模型分数直接比较**。密钥只从 `/home/hust/.config/m3-agent/bigmodel.env` 在运行时读取，未复制到本目录。
- 验证状态：τ² 安装检查、GLM 聊天及工具调用、`metaagent qualify`、一轮真实进化及 SkillFlow 单任务族容器评测均已完成。

## 已完成结果

| 检查或条件 | 结果 |
| --- | --- |
| `recuris check-data --benchmark tau2` | 全部通过 |
| `metaagent qualify` | PASS：受限 Read/Edit、越权拒绝、lint |
| Retail task 5、6，裸 Agent | 2/2；每题 1 次 |
| 同两题，确定性 M0 | 2/2；每题 1 次 |
| 同两题，作者发布记忆 | 1/2；每题 1 次 |
| 进化轮次 `glm_retail_one_round_v5_20260929` | 完整结束，28 次模拟，最终保留 M0 |

进化轮次用 task 41 作训练任务、task 6 作隔离验证，每题 4 次配对试验。M0 在训练任务为 0/4；GLM Meta-Agent 从失败轨迹生成候选记忆，涉及经验卡片、投递规则和工作记忆配置，候选通过静态检查。在修复筛选中，候选为 3/4、M0 为 0/4；在隔离验证中，候选为 3/4、M0 为 4/4。验证门记录净变化 −25 个百分点，**REJECT**；`state.json` 的最佳版本仍为 M0。这证明“轨迹 → 候选补丁 → 实际评测 → 回滚”流程运行成功，不能据此宣称策略改进。只有一个验证任务，结果也不足以估计跨任务效果。

## GLM 适配与可复查材料

- `glm_adaptation.patch`：将 τ² 固定推理档位从 GLM 不支持的 `medium` 改为 `low`，并在进化驱动中固定 GLM 为模拟用户参考模型。官方仓库其余逻辑未作为论文原配置声称。
- `run_glm_study.py`、`split_glm_one_round_41_k4.json`、`uv.lock`：运行入口、任务划分和依赖锁定。
- `plan.json`、`skill_memory_diff.patch`：Meta-Agent 的失败定位与候选记忆差异。
- `ledger.jsonl`、`round_1_finalize.json`、`provenance.json`：门控计算、回滚与来源记录。完整轨迹及运行日志保存在 node01 的 `ma_runs/glm_retail_one_round_v5_20260929/`。

## SkillFlow 单任务族结果

已取回官方指定源码提交 `7b49ff5` 并应用 Recuris 补丁。Hugging Face 主站在 node01 不可达，因此通过镜像下载了 `Production-Capacity-Planning` 任务族的 84 个有效文件（仅 3 个 `.DS_Store` 元数据文件未取得）。`recuris check-data --benchmark skillflow` 通过。Docker Engine 29.8.1、Compose 5.5.1 可用；基础镜像与 9 个任务镜像均已构建。

| 配对条件 | 正确任务 | 异常 |
| --- | ---: | ---: |
| 裸 Agent | 8/9 | 0 |
| 作者发布的 SkillFlow 记忆 | 8/9 | 0 |

`recuris skillflow score` 报告净差 **0 个百分点**，任务聚类 bootstrap 95% 区间为 **[−33.3, +33.3]** 个百分点；task1 从裸 Agent 的 0 变为记忆组的 1，task4 从 1 变为 0，其余七题相同。证据见 `skillflow_pair_score_envfix.json`。这只是一个任务族、每题一次的 GLM 改造配置，不能推断 SkillFlow 全基准效果，也不能对表论文原模型数值。

首次 Harbor 作业的 9 题均因 401 未评分：官方生成 YAML 中的 `${OPENAI_API_KEY}` 被当作字面字符串传入 Qwen Code。保留原 YAML，复制出 `*_envfix.yaml`，仅删除该占位字段，使 Harbor 从运行进程环境读取已配置密钥，并使用新的作业目录。成功结果只来自这组修正配置；两组均由 Qwen Code 0.24.6 调用 GLM-5.3-Flash，技能组的轨迹中已核验模板文本实际进入用户消息。`run_skillflow_glm_envfix.sh` 记录了无密钥落盘的运行入口。

构建 Ubuntu 基础镜像时 node01 无法访问 Docker Hub。镜像层通过可达的 HTTPS 镜像源按摘要下载、SHA-256 校验后导入 Docker；随后沿用 SkillFlow 原 Dockerfile 构建基础镜像，并为任务 Dockerfile 添加所需的本地兼容标签。基础镜像脚本中的部分 CLI 版本使用 `latest`，因此仅凭 Dockerfile 重新构建不能保证相同镜像；本次实际镜像已归档，精确恢复以归档为准。全量复现仍需下载完整 20 个任务族并匹配论文模型及评测环境。

## 后续多任务族重复试验

已将 SkillFlow 扩展到两个任务族、17 道题、每题每组两次，得到裸 Agent **32/34**、发布记忆 **33/34**；任务配对净差 +2.94 pp，95% 区间 [−5.88, +11.76] pp。源码适配、Qwen Code 版本、数据提交、配置与容器镜像 ID 均已固定，并归档实际运行镜像。设计、完整结果和复跑入口见 [multifamily_k2_README.md](multifamily_k2_README.md)。
