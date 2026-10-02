# R6 撞车校验报告（S7）

- 轮次：R6 Agent自进化RSI
- 校验日期：2026-10-01
- 事实来源：cards\ 下 80 张 L4/L3 精读卡（L4×40、L3×40；其中 WorldMM 有 arXiv/DOI 双卡，去重后 79 篇独立论文）
- 选题假设（受检对象）：**冻结基座模型下，围绕 M3-Agent 式多模态视频记忆，做"证据驱动的记忆错误定位 + 最小化局部修复"，并使修复沉淀为跨任务复用的记忆策略版本（递归策略进化）**；暂定题目《面向多模态智能体的证据驱动记忆修复与递归策略进化》。
- 语料边界：本轮去重后 4352 篇（OpenAlex+arXiv+SemanticScholar+Crossref 关键词/元数据检索）；深读 80 篇。

---

## 表 1 核心撞车工作（18 篇，按撞车风险降序）

> 字段说明：overlap_problem=与本题重叠的问题表述；overlap_mechanism=重叠的机制；overlap_assumption=共享的前提假设；overlap_dataset=重叠的评测对象；overlap_claim=重叠的主张；difference_from_ours=与本题差异；novelty_risk=新颖性风险（高/中/低）。

| # | 论文（cid） | 年份 | overlap_problem | overlap_mechanism | overlap_assumption | overlap_dataset | overlap_claim | publication_date | evidence | difference_from_ours | novelty_risk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Recuris**：Recursive Experiential–Working Memory Evolution（arxiv:2608.24876） | 2026 | "知道错了但不知修哪"——记忆更新粗粒度、弱定向 | 结构化 trace Γ→四组件归因（64.8% 定位精度实验：结构化 trace 64.8% vs 仅结果 13.0%）→只修补被归因组件（scoped patch）→验证门（修复源任务∧held-out 不回归） | 冻结 LLM；递归只发生在记忆控制层；跨任务/跨模型迁移 | τ²-Bench、SkillFlow、Terminal-Bench（文本工具调用） | "错误定位→局部修→门控准入"的 bounded 递归闭环已被系统证明 | 2026-08（v1，本地复现 2026-09-29 活跃） | 37/35 model-benchmark 对提升；τ²-Retail GPT-5.6 +17.8 | 域为文本技能/工作记忆组件，非 M3-Agent 类多模态视频记忆内容（错误实体链接/幻觉事件/时间错锚）；定位证据是 harness 内部结构化 trace，不需跨视觉-文本对齐；不修"记忆内容事实错误"本身 | **高**（概念框架最接近：闭环骨架逐项同构，必须作为首要对照与引用切割对象） |
| 2 | **Video-RSI**：视频理解 agent 的 harness 进化（arxiv:2609.37950，VideoHarness-RSI 后续） | 2026 | 执行轨迹只含当前 harness 获得的证据，竞争性失败解释（漏采样/感知错/证据误用）未决 | **Active Video Investigation**：改代码前回访原始视频区分失败解释（证据驱动定位的视频域首次实现）；cost-aware 双向门控准入 | 冻结 LLM（DeepSeek-V4-Pro）；离线演化+私有不相交选择集 | MLVU、LongVideoBench、Video-MME、EgoSchema | "用超出既有轨迹的证据做诊断"在视频域有效（消融：+8.2） | 2026-09 | 四基准超 VideoHarness-RSI 且帧数更少 | 修复对象是 harness 代码（prompt/工具/观察处理/记忆组件代码），不是记忆内容条目；无"这条记忆错了"的概念；无跨任务策略版本沉淀；诊断无定位精度量化 | **高**（视频+冻结+证据驱动诊断三要素同框；必须显式对比"harness 层 vs 记忆内容层"） |
| 3 | **HarnessFix**：失败轨迹诊断与 harness 缺陷修复（arxiv:2606.06324） | 2026 | 现有自我改进"绕过或临时压制错误而不修根因"、改进宽泛难归因 | HTIR 证据链中间表示（数据流+控制流+实现锚点）→症状定位→宽回溯→严裁决→层归属→缺陷合并→**scoped repair**（分层修复算子表）→回归感知验证；harness memory 复用补丁 | 冻结基座（明确排除改参数）；失败轨迹=结构化证据而非仅反馈信号 | GAIA、SWE-Bench-V、AppWorld、Terminal-Bench（文本 agent） | "诊断驱动、范围受限"的自动修复范式成立（平均 +11.1%） | 2026-06（v2） | 30 仓库/57,780 条开发记录实证；5 LLM 一致增益；跨模型迁移 +5.5–9.5% | 修 harness 工件（代码/prompt/配置）非记忆内容；Context/Memory 层缺陷修的是"记忆组装策略"，不审计记忆条目正确性；无多模态；跨任务=补丁复用非策略进化 | **高**（方法论模板同构：证据链→scoped 修复→回归验证；作为方法论合法性引用+域切割） |
| 4 | **ViLoMem**：视觉/逻辑双流 grow-and-refine 多模态语义记忆（arxiv:2511.21678） | 2025 | MLLM 重复犯相同错误；视觉感知错误级联引发逻辑幻觉 | 错误归因闭环（Verifier 判错→自动归因到视觉/逻辑流）→双流指南条目生成→**相似度门控 merge/create 局部更新**（grow-and-refine） | 冻结 MLLM（GPT-4.1/Qwen3-VL）；免训练；跨模型/跨基准复用 | MMMU、MathVista、HallusionBench 等 6 个多模态基准 | "错误归因驱动的多模态记忆更新+跨任务复用"已被占位（本池标定撞车风险：高） | 2025-11 | 6 基准一致增益；记忆可跨模型迁移 | 归因只到"视觉 vs 逻辑"二分类双流，无条目内细粒度错误定位（哪条记忆哪个成分错）；修复对象是解题"指南"而非视频记忆图内容（实体/事件/时间戳）；无策略进化层；非视频长程记忆场景 | **高**（冻结 MLLM+错误驱动多模态记忆+局部合并的最近邻，相关工作必须详述对比） |
| 5 | **CMMR-VLN**：持续多模态记忆检索的视觉语言导航（arxiv:2603.07997） | 2026 | VLN 智能体在相似路口重复犯错，缺乏经验复用 | Reflection 模块：失败→**定位"第一个错误决策步"**→三类错误类型化→把修正经验**写回出错 viewpoint 的记忆单元**（局部写入而非全局重写）；成功经验带过滤器替换 | 全冻结（GPT-4o prompt）；免训练经验积累 | R2R val unseen、真机 TurtleBot | "失败→首个错误步定位→定点写入记忆"已被实现（SR 相对 NavGPT +52.9%） | 2026-03 | 消融证明"经验必须规则化才有效"；真机验证 | 定位深度浅（单步 first-error+3 类手工标签，无多步证据链归因）；对象是外置经验库条目非视频记忆架构内部错误；无跨任务策略进化（仅导航域）；无验证门 | **高**（"错误定位+定点修复"组件在具身多模态域的先行者） |
| 6 | **AutoMem**：文本梯度驱动的记忆架构搜索 RSI（arxiv:2608.14621） | 2026 | 记忆架构高度耦合、任务特定，随机搜索浪费且不可归因 | **Failure-Guided Module Diagnosis**：失败 rollout 定位到 Encode/Store/Retrieve/Manage 四模块→定向 text gradient→受控模块级编辑→验证 | 冻结双骨干；不更新参数；架构搜索空间 valid-by-construction | GAIA、WebWalkerQA、xBench | "失败归因→架构局部修复"闭环在记忆系统层成立（GAIA 71.5%，+3.7） | 2026-08 | 单调超越随机搜索对照 | 修的是**记忆架构（模块配置）**而非**记忆内容（错误条目）**；定位靠 LLM 自由文本分析无证据链；纯文本无多模态 | **中高**（若把本题"修复"表述为调整记忆系统结构即被覆盖；必须钉死"记忆内容级"） |
| 7 | **ModularRSI**：模块化可泛化 harness 自改进（arxiv:2609.14857） | 2026 | harness RSI 泛化难：单轨迹歧义、机制级 credit assignment 缺失 | 同任务成败轨迹配对对比→五模块受限修改域独立演化→三重验证门（程序检查/diff 过特异性审查/执行验证）+回滚 | 冻结骨干；benchmark-disjoint 演化协议 | TerminalBench 2.0、SWE-Bench-V | "限制修改范围本身是增益来源"（joint 演化反而掉分） | 2026-09 | 模块化消融：52.43 vs joint 44.19 vs 基线 47.57；跨模型迁移为正 | 修复对象 harness 代码；文本域；对比信号是 rollout 成败而非多模态证据一致性 | **中高**（"scoped 修改+验证门"方法论同族；与 Recuris/AutoMem 构成文本域证据群） |
| 8 | **RRSI**：正则化递归 harness 自改进（arxiv:2609.24972） | 2026 | 递归演化过拟合：benchmark 专适配、噪声追逐、复杂度累积 | 编辑稀疏预算（L0）/证据感知 credit assignment/噪声地板接受/成本-收益约束（L2）/结构剪枝（L1）/泄漏筛查前置 | 完全冻结策略（Claude Opus 4.8/Gemini 3.5 Flash） | TB2.1、SWE-V、Harvey、EngDesign 等 8 基准 | "演化集收益与迁移收益解耦"（六个 held-out 全不回退） | 2026-09 | 比未正则化省 30% token、超基线 22.9% | 优化对象 harness 源码/提示非记忆内容；无错误定位环节（正则化选择而非诊断）；无多模态 | **中高**（其正则化四件套可直接移植为本题修复策略进化的准入设计，须引用并内化） |
| 9 | **MMA**：多模态记忆 agent 元认知可靠性层（arxiv:2602.16493） | 2026 | 相似度检索把过时/低可信/矛盾条目当等可靠证据 | 条目级置信分（来源+时间半衰期+冲突感知共识）→低置信触发 **abstain**（弃权）；MMA-Bench 信念动态基准 | 冻结（MIRIX 之上加层）；多模态（图文） | FEVER、LoCoMo、自建 MMA-Bench | "多模态记忆矛盾/不可靠条目的条目级定位与处置"已被占位（本池标定：中高） | 2026-02 | Visual Placebo Effect 命名与量化；Type-B 反转 41.18% vs 基线 0% | 只在检索时**降权/弃权**（post-retrieval 过滤，作者自述无法补召回缺失），不做库内条目的证据驱动改写修复；无跨任务策略进化 | **中高**（检索端降权/弃权族的代表，是本题必须划清的切割线之一） |
| 10 | **TAME**：可信测试时记忆进化（arxiv:2602.03224） | 2026 | 只用任务成功率为更新信号导致 Agent Memory Misevolution（能力升、可信度漂移） | Evaluator 对每条被用记忆评**贡献归因分**→Q 值降权（错误记忆被降权而非删除）+信任标注 | 冻结基座；流式进化仅用二元反馈 | AIME、GPQA、MMLU-Pro、Trust-Memevo | "证据（贡献归因）驱动的记忆质量控制"已成立 | 2026-02 | GPT-5.2 AIME 0.733 vs ReasoningBank 0.587 | "修复"=调 Q 值降权/打标签，不做错误内容定位改写与局部 patch；文本策略记忆；目标函数是可信度非任务能力 | **中高** |
| 11 | **VideoLoop**：循环工作记忆对抗语义颠簸（arxiv:2609.38119） | 2026 | 长视频 agent 的 append-only 工作记忆导致关键证据被稀释（semantic thrashing 形式化） | 内循环记忆编排器对 6 段结构化工作记忆发 **Update/Append/Delete 证据级编辑**（固定 32K 预算重写）；文件系统无损外存 | 冻结（Gemini 3.1 Pro/3 Flash）；token 成本近乎持平 | VideoMME-long、VideoMMMU、LongVideoBench | "任务内视频工作记忆的证据级删除-回填修复"已实现（+4.5，消融逐级验证） | 2026-09 | append-only 81.9 → 完整版 85.8（VideoMME-long） | 单视频问答**内**的实时维护，无跨任务经验沉淀、无策略进化、无持久记忆版本；对象是任务工作记忆非长期记忆库 | **中**（任务内记忆修复近邻；"跨任务进化"边界的切割对象） |
| 12 | **WorldMM**：动态多模态记忆 agent（arxiv:2512.02425 / doi:10.48550/arxiv.2512.02425，CVPR 2026） | 2025 | 长视频推理中视觉证据缺位、固定时间尺度失效 | semantic memory 增量 **Consolidate**：embedding 召回冲突三元组→LLM 裁决 T_remove/T_update→局部删改写入 | 全冻结 zero-shot | EgoLifeQA、Ego-R1、HippoVlog、LVBench、Video-MME | "多模态 KG 记忆的冲突检测→局部修删"写入口机制已成立（消融 −7%） | 2025-12 | 平均 69.5% 超最强基线 8.4% | 纯推理期静态管线：冲突只在写入时被相似度>0.6 触发、单次 LLM 裁决无验证；无任务失败驱动的回溯修复；无跨任务复用 | **中**（写入口冲突消解族的代表；可作为直接 baseline） |
| 13 | **ReflectWorld-MM**：实体导向多模态记忆系统（arxiv:2607.09759） | 2026 | M3-Agent 语义记忆 append-only、写入后无法修订/删除 | 可演化实体语义记忆：每 N 条观察触发 consolidate，输出 **Add/Update/Delete** 编辑决策+重要度增长方程；evidence/decision 分离身份解析 | 冻结（GPT-5/5-mini） | EgoLife-QA、M3-Bench、VideoMME-Long、LVBench、HippoVlog 六基准全第一 | "视频记忆需要可编辑（非 append-only）"已被社区明确并提出工程实现 | 2026-07 | EgoLife-QA 46.8 vs M3-Agent 30.8 | 编辑由固定周期触发，无证据驱动错误检测（错误事实靠下次 consolidate 碰撞才能纠正）；无修复闭环、无策略进化 | **中** |
| 14 | **MemEvolve**：记忆系统元进化（arxiv:2512.18746） | 2025 | 固定记忆架构无法元适应（二阶进化缺失） | Diagnose-and-Design：轨迹回放接口定位记忆行为缺陷→结构化缺陷画像→四模块受限重设计；Pareto 选母体 | 冻结基座（GPT-5-mini 等） | GAIA、WebWalkerQA、xBench、TaskCraft | "用轨迹回放证据做架构级诊断-再设计"已占位 | 2025-12 | GAIA pass@3 80.61 vs 无记忆 69.09；跨 LLM 迁移 +17.06 | 进化对象是整体架构代码，不做逐条记忆内容错误定位与局部修复；无多模态 | **高**（架构级元进化的占位者，本池原标高；内容级修复未被覆盖，风险集中在"记忆系统自进化"表述撞名） |
| 15 | **AgeMem**：统一长短期记忆管理的 RL（arxiv:2601.01885） | 2026 | LTM/STM 分立靠启发式，难端到端优化 | 把 **Add/Update/Delete**（条目级记忆修复原语）+Retrieve/Summary/Filter 并入动作空间，step-wise GRPO 训练；维护奖励显式激励"记忆纠错"行为 | 非冻结（RL 微调 Qwen2.5-7B/Qwen3-4B）——与本题冻结前提相斥 | ALFWorld、SciWorld、PDDL、BabyAI、HotpotQA | "记忆维护（更新/删除）可作为可学习动作被 RL 显式激励" | 2026-01 | 平均超最优基线 +4.82pp；记忆质量 MQ 最高 | 改权重；无证据驱动定位（何时改哪条全靠策略隐式学）；纯文本 | **中高**（"Update/Delete=记忆纠错"思想占位，但路线相斥可作强基线引证） |
| 16 | **MemSecBench**：记忆投毒从持久化到修复的追踪基准（arxiv:2607.27080） | 2026 | 恶意内容写入记忆后持久化并被召回，缺写入→后果→修复全链路评测 | Write–Execute–Forget 七 checkpoint 证据制判定；**SRSR=选择性修复成功率（恶意移除∧良性全保留）** | 隔离容器、固定 agent/model/环境配对比较；24 配置 | 自建 310 案例（code/science/daily/office，文本） | "修复时不伤及无关记忆是公认难点"（F1 86.3% vs F2 62.5%，SRSR 56.1%）；修复评测协议已建立 | 2026-07 | Judge-人标一致 90%+；修复是被动单轮 Forget | 对象是对抗性投毒非自然错误；是被评对象非修复方法；文本域、无多模态；无主动定位 | **低-中**（但其 SRSR/preservation 指标必须纳入本题评测） |
| 17 | **WorldMemArena**：动作-世界交互的多模态记忆评测（arxiv:2605.29341） | 2026 | 现有基准只报 QA 分，无法定位失败在写入/维护/检索/使用哪一环 | 四阶段生命周期诊断（Write/Maintain/Retrieve/Use）+gold memory points/update flags/superseded originals/evidence chains 标注 | 多模态长程任务；harness 记忆 agent 与手工管线对照 | 461 任务自建（Lifelong Evolution+Agentic Execution） | "当前系统只累积、极少修订或删除（append-only 主导）"的实证；多模态记忆仍是瓶颈 | 2026-05 | 四大发现含"存储召回高但 QA 证据召回大跌" | 诊断性基准不提供修复算法，无"发现→定位→修正→验证"闭环评测；无进化维度 | **中**（评测基础设施级重叠：其标注可直接用作本题定位模块的评测 GT） |
| 18 | **PAST-Bench**：个人 agent RSI 基础评测（arxiv:2608.04003） | 2026 | "保留的经验是否让 agent 随时间变好"从未被系统测试（性能归因难） | 配对 persistence on/off+四类对照 episode；**机制证据分（Mech）**判定增益是否走声称通路；Update 能力（二次写入覆写且旧值不泄漏）独立成轴 | 不重训不优化 prompt 的 online self-evolution | 26 场景 204 episodes 自建 | "同 headline 增益、通路证据悬殊"（Δ 差异小于 run-to-run 方差） | 2026-08 | 7 基座×4 框架 | 评测+人工设计机制的诊断研究，无自动修复闭环；文本个人助手域；无多模态 | **中**（评测协议模板：wrong-mechanism/stale 对照+机制证据分应内化为本题协议） |

### 表 1 补充：其余 61 篇的高风险信号（一句话）

- **综述族（gap 论证而非撞车）**：Storage-to-Experience 综述（arxiv:2605.06716）原话"多模态记忆绝大部分停留在 Storage 阶段，Reflection 与 Experience 阶段的工作极其稀缺"；Agent Memory 第二半综述（arxiv:2602.06052）§9.5 呼吁"action-conditioned 记忆更新与跨层一致性维护的原则性机制"、§9.6 呼吁"versioning/audit/rollback/provenance"；Graph-Memory 综述（arxiv:2602.05665）第一个 open challenge 即"记忆图质量如何被发现与度量"；记忆机制综述（arxiv:2603.07670）把"矛盾检测、可信反思、学会遗忘"列为一等开放问题；SSGM（arxiv:2603.11768）给出治理蓝图但无实验。
- **写时维护/信念修正族**：Infini Memory（arxiv:2606.10677，FC-MH 81.0→58.0 证明写时固化无法保证跨文档一致性）；DCPM（arxiv:2606.09483，supersedes 链上无纠错算子，作者自述失败模式）；MemCoRe（arxiv:2602.07885，Conflicts 仅作边标注）；BMAM（arxiv:2601.20465，再巩固+EMA 置信度，全局后台无逐条定位）；LightMem（arxiv:2604.07798，错误注入证明写入污染持续下游效应但系统无法自恢复）；MemVerse（arxiv:2512.03627，蒸馏会同样内化错误知识）；Light-Omni（arxiv:2607.05511，维护只有合并压缩一种算子）。
- **经验增删/进化族（文本）**：experience-following 实证（arxiv:2505.16067，错误传播问题意识，只删不改）；ReMe（arxiv:2512.10696，效用删除）；G-Memory（arxiv:2506.07398）；FORGE（doi:10.1145/3786335_3813155，整库广播替换）；SAGE 图记忆（arxiv:2605.12061，RL 写入策略）；RoMeRL（arxiv:2608.02508，Memory-Reward Trap）；PEAM（arxiv:2605.27762，失败-修正对参数内化）；KnowAct-GUIClaw（arxiv:2607.12625，技能修复优先于新抽取——技能域的"局部修复"）。
- **其他域平行实现**：ScienceBuddy（arxiv:2609.17523，内递归有界编辑+配对验证=验收协议同构）；MERID（arxiv:2609.36235，不确定性缩放接受裕度+保留裕度界——修复准入的统计基础）；RegenHarness（arxiv:2609.27612，物理域证据门控协议）；ASG-SI（arxiv:2512.23760，证据包治理，无实验）；材料科学家记忆（arxiv:2608.11224，沙盒反馈接地渐进修复，avoided-error rate 91.7%）；Harness substrate 评测（arxiv:2608.15008）。
- **安全侧动机**：MemLineage（arxiv:2605.14421，"Prevention is not recovery"原话=修复是 open problem 的直接证据）；MemoryGraft（arxiv:2512.16962）；OEP（arxiv:2605.18930，干净样本诱导错误规则固化）；A-MemGuard（arxiv:2510.02373）；MEXTRA（arxiv:2502.13172）。

---

## 表 2 撞车结论与处置建议

### 2.1 创新假设判定

**受检假设**："多模态记忆内容级的证据驱动错误定位 + 最小化局部修复 + 跨任务策略进化"（冻结基座）。

**判定：部分覆盖（PARTIALLY COVERED）——未被任何单一工作完整占位，但三个组成构件各自都有强先行者。**

| 构件 | 覆盖状态 | 占位者 | 剩余空间 |
|---|---|---|---|
| (a) 证据驱动的错误定位 | **文本域已成熟**（Recuris 结构化 trace 定位 64.8%、HarnessFix HTIR、ModularRSI 成败对比）；**视频域 harness 层已实现**（Video-RSI active investigation）、**具身经验条目层已实现浅版**（CMMR-VLN first-error） | Recuris / HarnessFix / Video-RSI / CMMR-VLN | **M3-Agent 类视频记忆图内部的条目级错误定位**（错误实体链接/幻觉事件/时间错锚/模态错配）无人做；多步证据链归因（首个错误≠根因）无人做；定位精度量化（对照 Recuris 的 64.8% 实验范式）在多模态域无人做 |
| (b) 最小化局部修复 | **写入口冲突消解已存在**（WorldMM Consolidate、ReflectWorld-MM Add/Update/Delete）；**任务内工作记忆编辑已实现**（VideoLoop）；**检索端降权/弃权已实现**（MMA/TAME）；**条目级 patch 原语已被 RL 学习**（AgeMem，改权重） | WorldMM / ReflectWorld-MM / VideoLoop / MMA / TAME / AgeMem | **任务失败驱动的事后（post-hoc）条目级修复**无人做——现有维护全部发生在写入时（Infini Memory FC-MH 81.0→58.0 证明写时固化无法保证跨条目一致性）或检索时（降权不补召回）；**修复的 preservation 约束**（良性记忆保留，MemSecBench 显示 SRSR 仅 56.1%、附带损伤是主因）无人在多模态记忆上机制化 |
| (c) 跨任务策略进化 | **文本技能/架构域已成熟**（Recuris 组件级 scoped patch+验证门、MemEvolve 架构元进化、AutoMem 模块搜索、RRSI 正则化）；**视频 harness 层已有**（Video-RSI 演化产物可复用） | Recuris / MemEvolve / AutoMem / Video-RSI | **修复策略（何时修、修哪、怎么修）作为跨视频/跨任务可版本化沉淀对象**无人做；Storage-to-Experience 综述明确把"从多模态轨迹簇提取模态不变策略先验"列为稀缺的未来工作 |

**综合结论**：假设的组合主张成立——"冻结基座 + 多模态视频记忆内容级 + 证据链定位 + 最小化 patch + 跨任务策略版本"五要素交集在 4352 篇语料的 80 篇深读中无人同时占据；但 (a)(b)(c) 单要素均高度活跃，2026 年上半年呈爆发态势（表 1 中 12/18 篇为 2026-02 之后），**撞车窗口正在快速关闭**。

### 2.2 处置建议：**保留选题，但改 RQ 表述 + 钉死机制限定 + 前置三类 baseline**

1. **保留**：核心组合假设未被推翻，差异点真实存在且有多篇综述背书（Storage-to-Experience、Agent Memory 第二半、Graph-Memory 三篇综述的 open challenges 逐条对应本题）。
2. **改 RQ**：研究问题从泛化的"记忆修复与自进化"收紧为——"在冻结基座的多模态视频记忆中，任务失败产生的跨模态证据链能否支持**条目级**错误定位（可量化定位精度），且**最小化 patch**（相比全量重写/重灌/检索端屏蔽）能在保住良性记忆（preservation）的前提下修复错误，并使修复策略跨视频迁移？"
3. **改机制（防御性设计，吸收撞车线教训）**：
   - 修复对象显式定义为**记忆内容条目及其依赖**（实体链接/事件/时间戳/模态证据），与 Recuris 的控制组件、AutoMem/MemEvolve 的架构模块、Video-RSI 的 harness 代码三层明确切割；
   - 定位证据必须**回访原始模态数据**（源片段/时间区间），对齐 Video-RSI 的 active investigation 并把对象从代码换成记忆条目；
   - 修复写入采用 append-only 版本链（supersedes，参考 RegenHarness/DCPM/MemLineage），支持回滚与审计；
   - 修复策略版本入库走**验证门控+不确定性缩放接受裕度**（Recuris 验证门 + MERID margin + RRSI 噪声地板/泄漏筛查），修复不得编码特定视频答案（防过拟合）。
4. **改实验假设（可证伪化）**：H1 定位有效性——证据链定位精度显著高于 trajectory-only 与 result-only（复刻 Recuris 13.0%/37.0%/64.8% 三条件实验到视频记忆域）；H2 局部性收益——等预算下最小化 patch 的 benign preservation 显著高于全量重建与 Recuris 风格直接适配；H3 跨任务迁移——策略版本在未见视频上带来净收益且六个 held-out 分割不回退（RRSI 协议）。
5. **降 baseline（必设对照）**：原始 M3-Agent；WorldMM/ReflectWorld-MM（写时维护）；MMA（检索端降权+弃权）；等预算额外检索/重试（VideoXAgent 式在线无记忆）；Recuris 风格直接适配（文本闭环搬到多模态记忆的最近竞争形态）；简单反思追加经验（Reflexion 式）。
6. **淘汰/降权**：无。本轮无工作要求放弃选题；唯 VideoLoop 与 CMMR-VLN 表明"任务内浅修复"已被占据，主张必须落在"跨任务策略版本"而非"修复动作本身"。

### 2.3 与两大相邻族的切割线（写作时必须在 Related Work 显式给出）

**切割线 1：与"修复 harness 工件"族（VideoHarness-RSI / Video-RSI / HarnessFix / ModularRSI / RRSI / ScienceBuddy / RegenHarness / NeoHorse-1 / Gödel Forest）**
- 他们：修改代理系统**外壳**——prompt、控制流、工具实现、观察处理、配置；记忆只是被组装的组件之一，不存在"这条记忆内容是错的"的判断；证据链锚回代码工件（文件/行号/模板）。
- 我们：修复对象是记忆架构**内部的持久内容状态**（实体/事件/时间戳/模态证据/依赖关系），定位证据链必须**跨模态对齐**（记忆声称 X 发生在 t——哪一帧/哪段音频支持或反驳它），这是文本 trace 无法表达的归因维度；修复产物沉淀为跨任务的**记忆策略版本**而非代码补丁。
- 一句话切割："他们让 agent 更会**组装**上下文，我们让 agent 修复**已存**的记忆。"

**切割线 2：与"检索端降权/弃权"族（MMA / TAME / SYNAPSE / E-mem / RoMeRL / A-MemGuard）**
- 他们：不动库内内容——给条目打置信标签、检索时降权、证据不足时拒答（abstain）；MMA 作者自述 post-retrieval 过滤**无法补召回缺失**；RoMeRL 的"替换"是效用坐标驱逐而非内容修正。
- 我们：库内条目的证据驱动定位-改写（错误内容被修正而非被屏蔽），修复后同一查询不再依赖弃权；且他们的置信信号（来源/时间/共识）恰可作为我们**候选错误定位的特征**而非终点——两族互补可引用为组件。
- 一句话切割："降权与弃权让错误记忆**不被使用**，修复让错误记忆**不再错误**。"

**补充切割线 3：与"写入口冲突消解"族（WorldMM / ReflectWorld-MM / MemCoRe / Infini Memory / Light-Omni / ScrapMem）**
- 他们：维护只发生在写入/固化时（周期性 consolidate、recency override、遗忘），无任务信号驱动的事后发现；Infini Memory 的 FC-MH（81.0→58.0）与 DCPM 自述失败模式（瞬时状态误判为稳定修订且无纠错算子）正是该范式上限的文献证据。
- 一句话切割："写时维护防新错，任务后修复清旧账。"

### 2.4 检索边界声明（必须随结论一并引用）

1. 本轮检索为 **关键词/元数据 API 检索**（OpenAlex 7 + arXiv 4 + SemanticScholar 2 + Crossref 1，共 14 条查询）；**backward snowballing（引文回溯）与 forward snowballing（前向引文追踪）未执行**；**embedding 语义向量检索未执行**。
2. 因此本报告的"未覆盖"结论仅为"在本轮语料（4352 篇）与 80 篇深读范围内未见占位者"，**不得表述为"没人做过"的绝对结论**；尤其 2026 年 9–10 月的最新 arXiv 与非 arXiv 渠道（ACL/NeurIPS 2026 cam-ready、GitHub 新仓库）覆盖有限。
3. 立项后建议补三个低成本动作：(a) 对 Recuris、Video-RSI、M3-Agent 三篇做 forward citation 监控（月频）；(b) 监控 ByteDance Seed（M3-Agent 团队）与 Gen-Verse（Recuris 团队）仓库的多模态/记忆方向 commit；(c) 在提交前用 Semantic Scholar 引文图对表 1 的 18 篇做一次 snowballing 复核。
4. 重复说明：本池深读 80 篇中 WorldMM 存在 arXiv/DOI 双卡（同文），独立论文数为 79；统计口径不影响上述判定。

---
*证据链：每行判定均可回溯至 cards\ 对应卡片（文件名即 cid）；funnel 口径见 funnel.json。*
