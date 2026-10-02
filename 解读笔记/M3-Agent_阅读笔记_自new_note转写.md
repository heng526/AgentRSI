<!-- 2026-10-01 由 new_note.xml（Notion 导出 XML 片段，UTF-8 完好，非乱码）转写为 Markdown；原文件移入 _待删除_请确认/。内容未作增删，仅格式转写（callout→引用块、grid 双栏→顺序排列、table→Markdown 表格、字面量 <face_1> 类记号→行内代码）。 -->

> 📌 **论文：**Seeing, Listening, Remembering, and Reasoning: A Multimodal Agent with Long-Term Memory（M3-Agent）
> **机构：**ByteDance Seed × 浙江大学 × 上海交通大学 ｜ arXiv: 2508.09736v4
> **一句话：**把持续到来的视频/音频流，转化为"情景记忆 + 语义记忆"，组织成以实体为中心的多模态记忆图；收到问题后，由 RL 训练的 Agent 多轮检索记忆并推理作答。

# 一、核心框架：感知—记忆—推理

M3-Agent 通过**两个并行过程**运作，关键在于**感知发生的时间**与**任务到来的时间**是分离的：

## 1.1 持续运行：记忆过程（Memorization）

Environment → Video / Audio → Memorization → Long-Term Memory

## 1.2 有任务时：控制过程（Control）

Instruction → Control → Search Memory → Reason → Response / Task

> 🔁 整体流程：**See / Listen → Remember → Retrieve → Reason**

记忆分为两类，类比人类认知：

> 🎬 **Episodic Memory 情景记忆**
> 具体经历、发生过的事件。例："Alice 拿起咖啡说我早上离不开这个""Alice 把空瓶扔进绿色垃圾桶"。

> 🧠 **Semantic Memory 语义记忆**
> 从经历中提炼的、可复用的抽象知识。例："Alice 早上喜欢喝咖啡""绿色垃圾桶用于回收"。

Memory = Face（人脸）+ Voice（人声）+ Textual Knowledge（文本知识），以 **Entity-Centric（实体为中心）**的 Graph Memory（图记忆）组织。

# 二、为什么需要长期记忆？（三个 WHY）

> ❓ 这三个 WHY 构成了 Introduction 的核心逻辑：逐一驳斥现有范式为何不够用。

## WHY-1：为什么 long context 不够？

Agent 面对的是**持续到来、理论上任意长度的 online multimodal stream**，而非一个有限的离线视频。现有 long-video 模型只是优化架构去处理"更长但有限"的视频，无法像人一样通过持续感知增量整合经验。

## WHY-2：为什么普通 video caption 不够？

普通视频描述关注局部事件，**难以持续维护人物身份、实体属性和世界知识**；长期累积后容易出现 ambiguity（歧义）和 inconsistency（不一致）。

## WHY-3：为什么普通 single-turn RAG 不够？

复杂问题需要**多次基于中间检索结果重新构造 query**，逐步收集证据。单轮检索一次往往信息是多维的、分散在多处，一次不一定查准查全。

# 三、两大关键挑战

## Challenge 1：无限信息流处理（Infinite Information Processing）

现有 long-video model 主要解决"如何一次处理一个很长但有限的视频"，而 Agent memory 要解决"如何**持续处理没有固定终点的数据流**"。

## Challenge 2：世界知识构建（World Knowledge Construction）

传统视频描述通常关注低层视觉细节，却容易忽略更高层的世界知识（Experience → Structured Knowledge）。缺乏这些高层知识，长期上下文就会产生歧义和不一致。

**M3-Agent 的解法：**通过 entity-centric memory structure（以实体为中心的记忆结构）**增量式构建世界知识**，为关键实体形成丰富的多模态表示，从而构建更连贯、更一致的长期记忆。

# 四、方法 Approach

## 4.1 长期记忆存放在哪里？

> 🗄️ **Memory ≠ Model Parameters**（不是模型参数）
> **Memory ≠ Context Window**（不是上下文窗口）
> **Memory = External Database**（外部数据库）

## 4.2 记忆结构：以实体为中心的多模态图

Memory 以 structured, multimodal format（text, images, audio）存储，组织为 **entity-centric multimodal graph**：

- M = (V, E)
- **V（节点）**：memory node，每个 node 是一条独立记忆单元（distinct memory item）
- **E（边）**：relationship edge，表示记忆项之间的逻辑关系；共享同一实体 ID 的节点互连

这种设计既支持按时间戳顺序检索，也支持按实体进行关联检索。

### 记忆节点长什么样？（Table 3）

| 属性 | 说明 |
|---|---|
| id | 节点唯一标识 |
| type | 模态类型：text / image / audio |
| content | 原始内容：纯文本 / base64 图像 / base64 音频 |
| embedding | 内容的向量表示，用于相似度检索 |
| weight | 数值，节点置信度 |
| extra_data | JSON 元数据，如时间戳 |

### 冲突解决：权重投票机制

新记忆加入时：与已有节点重复则 reactivate 并**提高 weight**；若是新知识则新增节点/边。冲突信息通过**权重投票**解决——频繁激活的高权重条目覆盖低权重的冲突条目，保证记忆图长期鲁棒一致。

### 搜索工具（Table 4）

| 函数 | 说明 |
|---|---|
| search_node | 接受 query 返回 top-k 最相关节点；支持 text / image / audio 多模态 query |
| search_clip | 返回 top-k 最相关记忆片段（某段约 30s clip 的 episodic + semantic memory） |

## 4.3 记忆生成（Memorization）

逐 clip 处理视频流（每段约 30 秒），生成 episodic + semantic 两类记忆。Semantic memory 不仅丰富内容，还提供额外检索线索。

### 一致的实体表示（Consistent Entity Representation）

核心难题：如何在任意长的时间跨度里保持主要人物/物体表示一致？

- 外挂**人脸识别**和**说话人识别**工具，提取 face_id / voice_id
- 所有记忆中人物必须用 face_id 或 voice_id 引用，如 "`<face_1>` 戴着红帽子、穿蓝色上衣"、"`<voice_2>` 对 `<face_3>` 说 How are you doing today"
- 通过 cross-modal reasoning 建立 **face-voice 等价**：推断某张脸和某个声音属于同一人，更新图中连接，统一为 character_id
- 相比文本描述（"一个留胡子的男人"），原始多模态身份特征更稳定，不易随时间漂移

## 4.4 控制与推理（Control）

收到指令后触发控制过程：Agent 自主**多轮推理 + 迭代记忆检索**，而非 single-turn RAG。每轮 policy πθ 输出 reasoning + action + argument：

action = [Search]：用 argument 查询记忆库，结果追加到上下文进入下一轮；可根据上下文灵活切换 search_node（查人）或 search_clip（查事件）action = [Answer]：输出答案，过程终止最多 H 轮（实验中 H = 5）

> 🔍 **实例（论文 Case Study）：**问"Tomasz 是想象力丰富还是缺乏想象力的人？"
> 第1轮：搜 Tomasz 的 character_id → 第2轮：直接问"他关于想象力的性格"，没搜到 → 第3轮：根据他是 CTO 这一信息，换角度搜"他的创意解决问题方式"→ 找到语义记忆"他有创新精神、前瞻性，热衷个人飞行无人机技术"→ 第4轮综合作答。

## 4.5 训练方式

| 阶段 | 基座模型 | 方法 |
|---|---|---|
| 记忆生成 | Qwen2.5-Omni-7b（多模态，支持音视频） | 模仿学习 SFT；合成数据三阶段：episodic 合成 + 身份等价检测 + 其他语义记忆合成 |
| 控制推理 | Qwen3-32b（语言模型，强推理） | 强化学习 DAPO；用 GPT-4o 评判答案对错作为 reward |
训练数据：500 个长视频 → 26,943 个 30 秒 clip → 2,736 条 QA pair。

# 五、M3-Bench 数据集

## 5.1 两个子集

| 子集 | 视频数 | QA 数 | 来源 |
|---|---|---|---|
| M3-Bench-robot | 100 | 1,276 | 机器人第一视角实拍；7 个家庭场景（客厅/厨房/卧室/书房/办公室/会议室/健身房）；67 名演员、51 个地点 |
| M3-Bench-web | 920 | 3,214 | YouTube 网络视频，46 个内容类别，覆盖更广 |

## 5.2 五类问题

| 类型 | 考察能力 | 示例 |
|---|---|---|
| Multi-evidence Reasoning | 汇总分散在多段的证据并比较 | 视频中五件拍品哪个起拍价最高？ |
| Multi-hop Reasoning | 跨段逐步追踪推理 | 去了丁茶之后去了哪家奶茶店？ |
| Cross-modal Reasoning | 结合视觉与音频信息 | 机密文件该放红色还是白色文件夹？ |
| Person Understanding | 人物身份/性格/关系 | Lucas 厨艺到底好不好？ |
| General Knowledge Extraction | 从具体事件提炼通用规则 | 蔬菜适合放冰箱哪一层？ |
现有 benchmark（EgoSchema、LongVideoBench、HourVideo、MVBench、Video-MME、MLVU）主要测试视觉理解（动作识别、时空感知），缺乏对**人物理解、通用知识提取、跨模态推理**这些依赖长期记忆的高层认知能力的考察。

# 六、实验结果

## 6.1 主结果（Table 5）

M3-Agent 在三个 benchmark 上全面超越所有 baseline：

| 方法 | robot (All) | web (All) | VideoMME-Long |
|---|---|---|---|
| Socratic Model (GPT-4o) | 8.5 | 28.7 | 38.8 |
| MA-LMM | 24.4 | 24.3 | 17.3 |
| Gemini-Agent（prompt） | 16.9 | 34.1 | 55.1 |
| Gemini-GPT4o-Hybrid（最强 baseline） | 24.0 | 41.2 | 56.5 |
| **M3-Agent** | **30.7** | **48.9** | **61.8** |

> 🏆 对比最强 baseline，M3-Agent 准确率提升：**robot +6.7%、web +7.7%、VideoMME-long +5.3%**。在 Person Understanding 和 Cross-modal Reasoning 两个维度提升尤为显著。

## 6.2 消融实验关键发现

> 🔥 **语义记忆至关重要：**去掉 semantic memory，准确率暴跌 17.1% / 19.2% / 13.1%。

- **身份等价（face-voice linking）：**去掉后 robot 从 30.7 掉到 19.5，影响巨大
- **RL 训练增益：**control-32b-prompt → control-32b-rl，提升 +10.0% / +8.0% / +9.3%
- **inter-turn instruction（轮间指令）：**去掉后降 10.5% / 5.8% / 5.9%
- **reasoning mode（推理模式）：**去掉后降 11.7% / 8.8% / 9.5%
- **DAPO vs GRPO：**DAPO 在所有测试集上始终优于 GRPO
- **模型规模：**DAPO 的收益随模型规模增大而增大（8b → 14b → 32b）

# 七、相关工作定位

已有四条路线，各有短板：

| 路线 | 做法 | 局限 |
|---|---|---|
| Long Context | 直接扩大上下文窗口 | 仍是 finite context，无法处理无限流 |
| Visual Token Compression | 压缩视觉 token 以延长时间覆盖 | 同上 |
| Memory-Based Video Methods | 把编码后的视觉特征存入记忆供检索 | 有视觉特征，但缺乏高层实体一致性 |
| Socratic Models | Video → 多模态模型 → 文本描述 → 记忆 | 有语义，但长期人物/实体描述容易不一致 |

> 🎯 **M3-Agent 的核心组合（差异化所在）：**
> Visual/Audio Identity（视觉/音频身份）+ Textual Knowledge（文本知识）+ Graph Structure（图结构）
> 既保留原始多模态身份特征，又抽取结构化知识，再用图结构把二者关联起来。

# 八、局限与未来方向

- **细粒度细节推理：**如"谁想吃火腿肠""帽子该挂高的还是矮的挂钩"——不可能把所有细节都记住，需要发展**选择性注意机制**，按任务聚焦相关细节
- **空间推理：**语言记忆对空间信息不如视觉记忆有效，未来长期记忆应引入**快照（snapshot）**等更丰富的视觉内容来支撑空间推理
