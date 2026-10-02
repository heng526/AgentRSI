# Recuris SkillFlow 多任务族、双重复配置

## 实验与结果

2026-09-29 在 node01 上运行两个任务族：`Production-Capacity-Planning`（9 题）和 `Cross-Format-Data-Reconciliation`（8 题）。每题在裸 Agent 与作者发布的技能记忆条件下各独立运行 2 次；每次 Harbor trial 只给 1 次尝试，作业按裸/记忆配对顺序执行，同组最大并发 3。Production 第一轮沿用此前的有效作业：新渲染配置与当时成功的 `envfix` 配置，除作业名和目录外完全一致，任务镜像 ID 未变。

| 任务族 | 裸 Agent | 发布记忆 | 净差 |
| --- | ---: | ---: | ---: |
| Cross-Format（8 题 × 2） | 16/16 | 16/16 | 0 pp |
| Production（9 题 × 2） | 16/18 | 17/18 | +5.56 pp |
| 合计（17 题 × 2） | **32/34** | **33/34** | **+2.94 pp** |

Recuris 评分器按任务聚类 bootstrap 的 95% 区间为 **[−5.88, +11.76] pp**，未排除零。逐题平均有 2 题改善、1 题回归：Production 的 task1、task7 各改善 0.5，task4 回归 0.5。两组共 68 条 trial 均有 verifier reward、无异常；17 道题各有 4 个不同运行 ID，任务校验和、模型名与 Qwen Code 版本在配对记录间一致。结果见 `multifamily_score_k2.json` 和 `multifamily_run_state.json`。

这属于 **GLM-5.3-Flash 改造配置**，只覆盖 SkillFlow 20 个任务族中的 2 个。模型服务端使用别名而非可验证的权重快照，Harbor 的两次运行也没有共同随机数种子，因此不把净差解读为显著收益或论文数值复现。

## 冻结内容

`multifamily_manifest.json` 是机器可读的来源清单：Recuris 提交和本地适配补丁、`uv.lock` 哈希、模型 ID 与 API Base URL、Qwen Code **0.24.6**、Docker 版本、两套基础镜像 ID、17 个任务镜像 ID、四份配置哈希、任务划分和数据清单哈希。`dataset_manifest.json` 固定 Hugging Face 数据提交 `ecaadb0e25d5d5cfd87bd86d81e77b4abe3a00bc`，列出 17 个任务与下载文件的 SHA-256。

node01 上还保存三个通过完整性测试的镜像归档：

| 归档（均在 `/home/hust/research_recuris/frozen/`） | SHA-256 |
| --- | --- |
| `skillflow-base-qwen0.24.6.tar.zst` | `79880bb4366226592247e553681af198c46afafa817487f88ebf0105599c7430` |
| `skillflow-base-pip-tuna.tar.zst` | `b34b9d565c3dfecc7bf31ce7d4503c03c646d52aed9b7e5016897552e13f338e` |
| `skillflow-task-images-k2.tar.zst` | `5fd1876d7dba6252a16582144a41980e259db694ea78bee0d0bccb6ee51e8513` |

第二套基础镜像只为 Cross-Format 的镜像构建指定清华 PyPI 镜像，解决原仓库下载 NumPy wheel 时停滞的问题；两个处理条件在**同一任务族内**使用相同任务镜像。Production 沿用原基础镜像。`Dockerfile.pip-mirror` 和两套镜像 ID 记录了这一环境差异。`build_skillflow_base_pinned.sh` 固定 Qwen Code 版本供重建使用；**精确恢复本轮环境以归档镜像为准**。

## 复跑入口

代码与数据位于 node01 的 `/home/hust/research_recuris/Recuris`，API 密钥只在进程启动时从 `/home/hust/.config/m3-agent/bigmodel.env` 读取。`glm_recuris_full_adaptation.patch` 包含官方源码的 GLM 适配，其中 SkillFlow 配置渲染器不再把 `${OPENAI_API_KEY}` 字面量写入 YAML，而由 Harbor/Qwen Code 使用进程环境变量。

在现有 node01 环境核验并续跑：

```bash
/home/hust/research_recuris/Recuris/.venv/bin/python \
  /home/hust/research_recuris/run_multifamily_k2.py --check-only
/home/hust/research_recuris/launch_multifamily_k2.sh
```

第二条命令会跳过已完整通过校验的作业；若要获得全新独立重复，应在新的隔离实验目录和新的作业名下运行，不覆盖本轮结果。恢复归档镜像时执行：

```bash
cd /home/hust/research_recuris/frozen
zstd -dc skillflow-base-qwen0.24.6.tar.zst | docker load
docker tag skillflow/harbor-cli-base:ubuntu24.04 skillflow/harbor-cli-base:qwen0.24.6-orig
zstd -dc skillflow-base-pip-tuna.tar.zst | docker load
docker tag recuris/skillflow-base:pip-tuna skillevlove/harbor-cli-openhands:ubuntu24.04
zstd -dc skillflow-task-images-k2.tar.zst | docker load
```

任务数据可用 `download_pinned_skillflow.py` 按上述提交重新下载并与 `dataset_manifest.json` 的哈希核对。
