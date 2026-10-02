# P01 — Memory in the Age of AI Agents: A Survey

## B01 | Paper information, Abstract, Figure 1, and §1 Introduction

**Source:** Memory in the Age of AI Agents A Survey_1-77.pdf  
**Source pages:** PDF pp. 1–5, plus the §1 closing text at the top of p. 6  
**Batch status:** COMPLETED  
**Scope note:** The original §1 ends before §2 on PDF p. 6. Its last two paragraphs are included here so that the Introduction is not split. The §2 heading and all §2 content belong to B02.

## Paper Information | 论文信息

- **Title:** *Memory in the Age of AI Agents: A Survey — Forms, Functions and Dynamics*
- **Chinese reading title:** *AI 智能体时代的记忆：综述——形式、功能与动态*
- **Authors:** Yuyang Hu et al. The complete author roster and affiliations are preserved from the source cover for the final reading edition; affiliation addresses are not translated.
- **Version:** arXiv:2512.13564v2, 13 January 2026.
- **Type:** Survey.
- **Source-grounded topic:** Agent memory, organised by **forms**, **functions**, and **dynamics**.
- **Research relevance:** Directly relevant as a conceptual foundation for *Multimodal Memory for Embodied Agents*, especially the paper’s distinctions between memory, LLM memory, RAG, and context engineering, and its later multimodal-memory frontier.

## Abstract | 摘要

### Original | 英文原文

Memory has emerged, and will continue to remain, a core capability of foundation model-based agents. It underpins long-horizon reasoning, continual adaptation, and effective interaction with complex environments. As research on agent memory rapidly expands and attracts unprecedented attention, the field has also become increasingly fragmented. Existing works that fall under the umbrella of agent memory often differ substantially in their motivations, implementations, assumptions, and evaluation protocols, while the proliferation of loosely defined memory terminologies has further obscured conceptual clarity. Traditional taxonomies such as long/short-term memory have proven insufficient to capture the diversity and dynamics of contemporary agent memory systems. This survey aims to provide an up-to-date and comprehensive landscape of current agent memory research. We begin by clearly delineating the scope of agent memory and distinguishing it from related concepts such as LLM memory, retrieval augmented generation (RAG), and context engineering. We then examine agent memory through the unified lenses of forms, functions, and dynamics. From the perspective of forms, we identify three dominant realizations of agent memory, namely token-level, parametric, and latent memory. From the perspective of functions, we move beyond coarse temporal categorizations and propose a finer-grained taxonomy that distinguishes factual, experiential, and working memory. From the perspective of dynamics, we analyze how memory is formed, evolved, and retrieved over time as agents interact with their environments. To support empirical research and practical development, we compile a comprehensive summary of representative benchmarks and open source memory frameworks. Beyond consolidation, we articulate a forward-looking perspective on emerging research frontiers, including automation-oriented memory design, the deep integration of reinforcement learning with memory systems, multimodal memory, shared memory for multi-agent systems, and trustworthiness issues. We hope this survey serves not only as a reference for existing work, but also as a conceptual foundation for rethinking memory as a first-class primitive in the design of future agentic intelligence.

### Translation | 中文翻译

记忆已经成为，并且将继续作为基于基础模型的智能体（foundation model-based agents）的核心能力。它支撑着长时程推理（long-horizon reasoning）、持续适应（continual adaptation），以及同复杂环境进行有效交互。随着 agent memory（智能体记忆）研究快速扩张并获得前所未有的关注，这一领域也日益碎片化。被归入 agent memory 范畴的现有工作，常常在其动机、实现、假设和评估协议上存在显著差异；与此同时，大量定义不够严格的记忆术语不断涌现，进一步模糊了概念边界。诸如长/短期记忆（long/short-term memory）这样的传统分类法，已被证明不足以刻画当代 agent memory 系统的多样性及其动态性。

本综述旨在给出当前 agent memory 研究的最新、全面图景。我们首先清晰界定 agent memory 的范围，并将它与 LLM memory（大语言模型记忆）、retrieval augmented generation（RAG，检索增强生成）以及 context engineering（上下文工程）等相关概念区分开来。随后，我们从 forms（形式）、functions（功能）和 dynamics（动态）这三个统一视角考察 agent memory。从形式的角度，我们识别出 agent memory 的三种主导实现形态：token-level memory（词元级记忆）、parametric memory（参数记忆）和 latent memory（潜在记忆）。从功能的角度，我们超越粗粒度的时间性分类，提出一个更细致的分类法，区分 factual memory（事实记忆）、experiential memory（经验记忆）与 working memory（工作记忆）。从动态的角度，我们分析智能体在与环境交互时，记忆如何随时间形成、演化并被检索。

为支持实证研究和实际开发，我们汇总了代表性 benchmark（基准）以及开源 memory framework（记忆框架）。除综合梳理已有工作之外，我们还以前瞻性的视角阐述了若干新兴研究前沿，包括面向自动化的记忆设计、reinforcement learning（RL，强化学习）与记忆系统的深度整合、多模态记忆、多智能体系统的共享记忆，以及可信性问题。我们希望本综述不仅能作为现有工作的参考资料，也能成为重新思考记忆的概念基础：在未来 agentic intelligence（智能体智能）的设计中，将记忆视为一项一等原语（first-class primitive）。

### Paper Role | 这段在论文里起什么作用

[Paper] 摘要先说明 agent memory 的重要性与概念碎片化问题，再明确整篇 Survey 的三条组织轴：**Form → Function → Dynamics**。它也预告了与本项目最直接相关的两个位置：概念边界比较（§2）和 multimodal memory（§7.4）。

## Contents | 目录处理说明

[Paper] 原论文目录位于 PDF pp. 2–3，列出了 §1–§8、各级小节及起始页。  
[Translation] 最终 DOCX/PDF 将生成可点击/可更新的双语目录，保留作者的章节编号与原始英文标题；目录条目会紧跟中文标题。为避免将目录与正文重复，本批不逐行复写两页原始目录。

## Figure 1

### Figure 1 — Original Figure | 作者原图

[Paper] Source location: PDF p. 4, upper half. The original figure asset is preserved for final insertion; it is not redrawn or altered in this working batch.

### Original Caption | 原始英文图注

Figure 1 Overview of agent memory organized by the unified taxonomy of forms (Section 3), functions (Section 4), and dynamics (Section 5). The diagram positions memory artifacts by their dominant form and primary function. It further maps representative systems into this taxonomy to provide a consolidated landscape.

### 中文图注

图 1：按照 forms（形式，第 3 节）、functions（功能，第 4 节）与 dynamics（动态，第 5 节）这一统一分类法组织的 agent memory 概览。该图依据记忆工件（memory artifacts）的主导形式和主要功能对其进行定位；它还将代表性系统映射到这一分类体系中，以提供一个整合性的领域全景。

### Figure Walkthrough | 图解

[Paper] 这不是一条“观测 → 动作”的 agent pipeline 图，而是一张**分类定位图**。阅读时先从图底部的 **Diverse Memory Forms** 开始：横向的三个位置分别是 Token-level Memory、Parametric Memory 和 Latent Memory。再沿右侧斜向的标签辨认功能维度：Factual Memory、Experiential Memory、Working Memory，并结合 Long-term / Short-term 的标识理解时间跨度。

[Paper] 图中的椭圆/节点把不同 memory artifact 放入“形式 × 功能”的空间中；向上的虚线将这些位置连接到代表性的机制/系统群组。例如，左侧列出了 Context Condensation、Extract Insights、Multimodal RAG、Knowledge Graph、Model & Knowledge Editing；上方和右侧则出现 Context Branching、Internalizing Experiences、KV Generation、KV Reuse/Compression 与 Latent Memory Generation。作者借这些实例说明：同样被叫作“memory”的系统，可能在载体、用途和运行方式上根本不同。

[Analysis] 对你的课题而言，最重要的启示是：不要因为一个系统保存了历史视频、caption、scene graph 或 vector database 就直接把它归为同一种“多模态记忆”。后续阅读必须分别记录它的 representation、write/update/retrieve 机制，以及 retrieval 是否真的进入 planner/policy 并改变 action。

### Grayscale Reading Guide | 黑白阅读说明

[Analysis] 原图含有浅青、青绿、粉色等填充色。黑白打印时，应优先依据**底部三种 memory form 的文字位置、右侧功能标签、节点形状及与上方方法群的虚线连接**识别含义，不以颜色本身作为唯一依据。最终版将保留作者原图，并在图下保留本说明；若实际灰度 QA 显示填充区仍难分辨，会附加明确标记为“辅助重绘”的黑白示意，而不会篡改作者原图。

# 1 Introduction

## 1 引言

### Original | 英文原文

The past two years have witnessed the overwhelming evolution of increasingly capable large language models (LLMs) into powerful AI agents (Matarazzo and Torlone, 2025; Minaee et al., 2025; Luo et al., 2025a). These foundation-model-powered agents have demonstrated remarkable progress across diverse domains such as deep research (Xu and Peng, 2025; Zhang et al., 2025p), software engineering (Wang et al., 2024i), and scientific discovery (Wei et al., 2025c), continuously advancing the trajectory toward artificial general interlligence (AGI) (Fang et al., 2025a; Durante et al., 2024). Although early conceptions of “agents” were highly heterogeneous, a growing consensus has since emerged within the community: beyond a pure LLM backbone, an agent is typically equipped with capabilities such as reasoning, planning, perception, memory, and tool-use. Some of these abilities, such as reasoning and tool-use, have been largely internalized within model parameters through reinforcement learning (Wang et al., 2025m; Qu et al., 2025b), while some still depend heavily on external agentic scaffolds. Together, these components transform LLMs from static conditional generators into learnable policies that can interact with diverse external environments and adaptively evolve over time (Zhang et al., 2025f; Liu et al., 2025a).

### Translation | 中文翻译

过去两年见证了能力不断增强的 large language models（LLMs，大语言模型）向强大 AI agents（人工智能体）的快速演进（Matarazzo and Torlone, 2025; Minaee et al., 2025; Luo et al., 2025a）。这些由基础模型驱动的智能体（foundation-model-powered agents）已经在 deep research（深度研究）（Xu and Peng, 2025; Zhang et al., 2025p）、software engineering（软件工程）（Wang et al., 2024i）和 scientific discovery（科学发现）（Wei et al., 2025c）等不同领域展现出显著进展，并持续推动通向 artificial general interlligence（AGI，通用人工智能）的发展轨迹（Fang et al., 2025a; Durante et al., 2024）。尽管早期对“agents”的理解高度异质，但学界随后逐渐形成共识：除纯粹的 LLM backbone（主干模型）外，一个智能体通常还配备 reasoning（推理）、planning（规划）、perception（感知）、memory（记忆）和 tool-use（工具使用）等能力。其中一些能力，例如推理和工具使用，已通过 reinforcement learning（强化学习）在很大程度上内化于模型参数之中（Wang et al., 2025m; Qu et al., 2025b）；另一些能力仍高度依赖外部的 agentic scaffolds（智能体支架）。这些组件共同把 LLM 从静态的条件生成器（conditional generators）转化为可学习的 policy（策略）：该策略能够与多样的外部环境交互，并随时间自适应地演化（Zhang et al., 2025f; Liu et al., 2025a）。

[Source note] 原文将 “artificial general intelligence” 拼为 “artificial general interlligence”。英文原文按 PDF 保留；中文按其显然指向的术语“通用人工智能”翻译，不把该拼写错误当作技术主张。

### Original | 英文原文

Among these agentic faculties, memory stands out as a cornerstone, explicitly enabling the transformation of static LLMs, whose parameters cannot be rapidly updated, into adaptive agents capable of continual adaptation through environmental interaction (Zhang et al., 2025s; Wu et al., 2025g). From an application perspective, numerous domains demand agents with proactive memory management rather than ephemeral, forgetful behaviors: personalized chatbots (Chhikara et al., 2025; Li et al., 2025b), recommender systems (Liu et al., 2025c), social simulations (Park et al., 2023; Yang et al., 2025), and financial investigations (Zhang et al., 2024) all rely on the agent’s ability to process, store, and manage historical information. From a developmental standpoint, one of the defining aspirations of AGI research is to endow agents with the capacity for continual evolution through environment interactions (Hendrycks et al., 2025), a capability fundamentally grounded in agent memory.

### Translation | 中文翻译

在这些智能体能力中，memory（记忆）尤为关键：它明确地使静态 LLM——其参数无法被快速更新——能够转变为可通过环境交互实现持续适应（continual adaptation）的自适应智能体（Zhang et al., 2025s; Wu et al., 2025g）。从应用角度看，许多领域需要智能体进行主动的 memory management（记忆管理），而不是表现出短暂、易遗忘的行为：personalized chatbots（个性化聊天机器人）（Chhikara et al., 2025; Li et al., 2025b）、recommender systems（推荐系统）（Liu et al., 2025c）、social simulations（社会模拟）（Park et al., 2023; Yang et al., 2025）和 financial investigations（金融调查）（Zhang et al., 2024），都依赖智能体处理、存储和管理历史信息的能力。从发展角度看，AGI 研究的一个标志性追求，是赋予智能体通过环境交互持续演化的能力（Hendrycks et al., 2025）；而这种能力在根本上建立于 agent memory 之上。

### Original | 英文原文

Agent Memory Needs A New Taxonomy Given the growing significance and community attention surrounding agent memory systems, it has become both timely and necessary to provide an updated perspective on contemporary agent memory research. The motivation for a new taxonomy and survey is twofold: ❶ Limitations of Existing Taxonomies: While several recent surveys have provided valuable and comprehensive overviews of agent memory (Zhang et al., 2025s; Wu et al., 2025g), their taxonomies were developed prior to a number of rapid methodological advances and therefore do not fully reflect the current breadth and complexity of the research landscape. For example, emerging directions in 2025, such as memory frameworks that distill reusable tools from past experiences (Qiu et al., 2025a,c; Zhao et al., 2025c), or memory-augmented test-time scaling methods (Zhang et al., 2025g; Suzgun et al., 2025), remain underrepresented in earlier classification schemes. ❷ Conceptual Fragmentation: With the explosive growth of memory-related studies, the concept itself has become increasingly expansive and fragmented. Researchers often find that papers claiming to study “agent memory” differ drastically in implementation, objectives, and underlying assumptions. The proliferation of diverse terminologies (declarative, episodic, semantic, parametric memory, etc.) further obscures conceptual clarity, highlighting the urgent need for a coherent taxonomy that can unify these emerging concepts.

### Translation | 中文翻译

**Agent Memory 需要新的分类法。**鉴于 agent memory systems（智能体记忆系统）的重要性和社区关注度不断上升，现在既恰逢其时，也有必要为当代 agent memory 研究给出一个更新后的视角。提出新分类法和本综述有两方面动机：❶ **现有分类法的局限性：**虽然若干近期综述已对 agent memory 给出了有价值且全面的概览（Zhang et al., 2025s; Wu et al., 2025g），但它们的分类法形成于一系列快速方法学进展之前，因此未能充分反映当前研究图景的广度和复杂性。例如，2025 年出现的一些新方向——从过去经验中蒸馏出可复用工具的 memory frameworks（记忆框架）（Qiu et al., 2025a,c; Zhao et al., 2025c），或 memory-augmented test-time scaling methods（记忆增强的测试时扩展方法）（Zhang et al., 2025g; Suzgun et al., 2025）——在更早的分类体系中仍未得到充分呈现。❷ **概念碎片化：**随着 memory-related studies（记忆相关研究）的爆炸式增长，这一概念本身变得愈发宽泛和碎片化。研究者常常发现，声称研究“agent memory”的论文在实现、目标和底层假设方面存在巨大差异。多样术语（declarative、episodic、semantic、parametric memory 等）的不断增殖，进一步遮蔽了概念清晰性，凸显出需要一套能够统一这些新兴概念的连贯分类法。

### Original | 英文原文

Therefore, this paper seeks to establish a systematic framework that reconciles existing definitions, bridges emerging trends, and elucidates the foundational principles of memory in agentic systems. Specifically, this survey aims to address the following key questions:

Key Questions  
❶ How is agent memory defined, and how does it relate to related concepts such as LLM memory, retrieval-augmented generation (RAG), and context engineering?  
❷ Forms: What architectural or representational forms can agent memory take?  
❸ Functions: Why is agent memory needed, and what roles or purposes does it serve?  
❹ Dynamics: How does agent memory operate, adapt, and evolve over time?  
❺ What are the promising frontiers for advancing agent memory research?

### Translation | 中文翻译

因此，本文试图建立一个系统化框架：它协调既有定义，连接新兴趋势，并阐明 agentic systems（智能体系统）中记忆的基础原则。具体而言，本综述旨在回答以下关键问题：

**关键问题**  
❶ 如何定义 agent memory？它与 LLM memory、retrieval-augmented generation（RAG，检索增强生成）和 context engineering（上下文工程）等相关概念有何关系？  
❷ **形式（Forms）：**agent memory 能采取哪些架构或表示形式（representational forms）？  
❸ **功能（Functions）：**为什么需要 agent memory？它承担哪些作用或目的？  
❹ **动态（Dynamics）：**agent memory 如何运行、适应并随时间演化？  
❺ 推进 agent memory 研究的有前景前沿是什么？

### Original | 英文原文

To address question ❶, we first provide formal definitions for LLM-based agents and agent memory systems in Section 2, and present a detailed comparison between agent memory and related concepts such as LLM memory, RAG, and context engineering. Following the “Forms–Functions–Dynamics” triangle, we offer a structured overview of agent memory. Question ❷ examines the architectural forms of memory, which we discuss in Section 3, highlighting three mainstream implementations: token-level, parametric, and latent memory. Question ❸ concerns the functional roles of memory, addressed in Section 4, where we distinguish between factual memory, which records knowledge from agents’ interactions with users and the environment; experiential memory, which incrementally enhances the agent’s problem-solving capabilities through task execution; and working memory, which manages workspace information during individual task instances. Question ❹ focuses on the lifecycle and operational dynamics of agent memory, which we present sequentially in terms of memory formulation, retrieval, and evolution.

### Translation | 中文翻译

为回答问题 ❶，我们首先在第 2 节给出 LLM-based agents（基于 LLM 的智能体）和 agent memory systems 的形式化定义，并详细比较 agent memory 与 LLM memory、RAG 和 context engineering 等相关概念。遵循“Forms–Functions–Dynamics（三角）”，我们给出 agent memory 的结构化概览。问题 ❷考察记忆的架构形式，第 3 节将讨论这一问题，并突出三种主流实现：token-level memory、parametric memory 与 latent memory。问题 ❸涉及记忆的功能角色，第 4 节将回答这一问题；该节区分 factual memory——记录智能体与用户、环境交互中得到的知识——experiential memory——通过任务执行逐步提高智能体的问题求解能力——以及 working memory——管理单个任务实例期间的工作空间信息。问题 ❹聚焦 agent memory 的生命周期和运行动态；我们将按 memory formulation（记忆构建）、retrieval（检索）和 evolution（演化）的顺序进行阐述。

### Original | 英文原文

After surveying existing research through the lenses of “Forms–Functions–Dynamics,” we further provide our perspectives and insights on agent memory research. To facilitate knowledge sharing and future development, we first summarize key benchmarks and framework resources in Section 6. Building upon this foundation, we then address question ❺ by exploring several emerging yet underdeveloped research frontiers in Section 7, including automation-oriented memory design, the integration of reinforcement learning (RL), multimodal memory, shared memory for multi-agent systems, and trustworthy issues.

### Translation | 中文翻译

在通过“Forms–Functions–Dynamics”的视角综述现有研究之后，我们进一步给出对 agent memory 研究的观点与洞见。为促进知识共享和未来发展，我们首先在第 6 节总结关键 benchmark（基准）与 framework（框架）资源。在此基础上，我们随后在第 7 节探索若干新兴但尚未充分发展的研究前沿，以回答问题 ❺；这些前沿包括面向自动化的记忆设计、reinforcement learning（RL，强化学习）的整合、多模态记忆、多智能体系统的共享记忆，以及可信性问题。

### Original | 英文原文

Contributions The contributions of this survey can be summarized as follows: (1) We present an up-to-date and multidimensional taxonomy of agent memory from the perspective of “forms–functions–dynamics,” offering a structured lens through which to understand current developments in the field. (2) We provide an in-depth discussion on the suitability and interplay of different memory forms and functional purposes, offering insights into how various memory types can be effectively aligned with distinct agentic objectives. (3) We investigate emerging and promising research directions in agent memory, thereby outlining future opportunities and guiding pathways for advancement. (4) We compile a comprehensive collection of resources, including benchmarks and open-source frameworks, to support both researchers and practitioners in further exploration of agent memory systems.

### Translation | 中文翻译

**贡献。**本综述的贡献可概括为：  
（1）我们从“forms–functions–dynamics”的视角提出一个最新的、多维度的 agent memory 分类法，为理解该领域当前发展提供结构化视角。  
（2）我们深入讨论不同 memory forms（记忆形式）与 functional purposes（功能目的）的适用性和相互关系，从而说明如何使各类记忆与不同智能体目标有效对齐。  
（3）我们考察 agent memory 中新兴且有前景的研究方向，从而勾勒未来机会并给出推进路径。  
（4）我们汇编了包括 benchmarks 和 open-source frameworks（开源框架）在内的综合资源集合，以支持研究者和实践者进一步探索 agent memory systems。

### Original | 英文原文

Outline of the Survey The remainder of this survey is organized as follows. Section 2 formalizes LLM-based agents and agent memory systems, and clarifies their relationships with related concepts. Section 3, Section 4, and Section 5 respectively examine the forms, functions, and dynamics of agent memory. Section 6 summarizes representative benchmarks and framework resources. Section 7 discusses emerging research frontiers and future directions. Finally, we conclude the survey with a summary of key insights in Section 8.

### Translation | 中文翻译

**综述结构。**本综述余下部分安排如下：第 2 节形式化定义 LLM-based agents 和 agent memory systems，并澄清它们与相关概念的关系。第 3、4、5 节分别考察 agent memory 的 forms、functions 和 dynamics。第 6 节总结代表性 benchmarks 和 framework resources。第 7 节讨论新兴研究前沿与未来方向。最后，第 8 节以关键洞见的总结结束本综述。

## Section Takeaway | 本节核心

- [Paper] 作者认为传统的 long-term / short-term 二分法不足以描述当代 agent memory 的机制差异与生命周期。
- [Paper] 本文的主分类框架是三个正交视角：**Form（以什么载体存）— Function（为解决什么能力问题而存）— Dynamics（如何形成、演化和检索）**。
- [Paper] 作者明确承诺在 §2 区分 agent memory、LLM memory、RAG 与 context engineering；这是后续判断“某方法究竟算不算 Agent Memory”的证据入口。
- [Paper] 该 Survey 将 factual、experiential、working memory 作为功能分类，而不是只按保存时间分类。
- [Paper] 多模态记忆、RL 整合、自动化 memory management、共享记忆与可信性被作者列为前沿；具体证据需到 §7 阅读，不能仅根据本节将其当成已验证结论。
- [Analysis] 对具身多模态记忆而言，这个三轴框架仍不够充分：它尚未在本节规定 spatial/temporal grounding、object permanence、partial observability、action-conditioned write/read 等维度。后续应把这些视为对 Survey 框架的**具身化补充轴**，而非误当成作者在本节已提出的分类。

## Academic English | 科研英语

| Expression / sentence pattern | 当前语境中的含义 | 写作作用 |
|---|---|---|
| **The past two years have witnessed ...** | “过去两年见证了……的发展/变化。” | 引言中快速交代近年的趋势与研究背景。 |
| **stands out as a cornerstone** | “作为一个基石而尤为突出。” | 强调某个模块在系统中不可替代的重要性。 |
| **fall under the umbrella of X** | “被笼统地归入 X 的范畴。” | 先指出一个大标签，再批评其中对象并不一致。 |
| **This paper seeks to establish ...** | “本文试图建立……。” | 明确论文目标，但语气比“证明”更审慎。 |
| **Following the ... triangle, we offer ...** | “遵循……三角框架，我们给出……。” | 说明文章组织/分类依据。 |
| **Building upon this foundation, ...** | “在这一基础上，……” | 表示后文依赖前文已经建立的概念或资源。 |

## P01 Glossary — initial entries | 初始术语表

| English term | 中文简单解释 / consistent translation | First appearance |
|---|---|---|
| foundation model-based agent | 基于基础模型的智能体；以 foundation model 为核心、可结合外部组件的智能体 | Abstract |
| agent memory | 智能体记忆；需要在 §2 再以作者正式定义校准 | Abstract |
| long-horizon reasoning | 长时程推理；覆盖较长交互/任务链的推理 | Abstract |
| continual adaptation | 持续适应；在环境交互中持续调整能力/行为 | Abstract |
| LLM memory | 大语言模型记忆；与 agent memory 的边界待 §2 处理 | Abstract |
| retrieval augmented generation (RAG) | 检索增强生成 | Abstract |
| context engineering | 上下文工程 | Abstract |
| token-level memory | 词元级记忆 | Abstract |
| parametric memory | 参数记忆 | Abstract |
| latent memory | 潜在记忆 | Abstract |
| factual memory | 事实记忆 | Abstract |
| experiential memory | 经验记忆 | Abstract |
| working memory | 工作记忆 | Abstract |
| agentic scaffold | 智能体支架；承载 LLM 外部能力的系统性结构 | §1 |
| first-class primitive | 一等原语；系统设计中被直接、基础地对待的能力/对象 | Abstract |

## Research Notes | 研究注记

[Paper] 作者的直接论断是：agent memory 研究在动机、实现、假设和评估协议上高度异质，需要新的多维分类法。  

[Inference] 如果 §2 对“read/write interaction with decision process”的形式化定义成立，那么仅把历史轨迹塞进长 context 的系统，未必满足作者所说的 agent memory lifecycle；需逐项核验 write、store、retrieve 与 policy coupling。  

[Analysis] 这正对齐你的长期问题：成熟 text-agent memory 的“语义总结 + embedding 检索”若没有空间、时间、对象和 action 条件，就无法仅凭“memory”标签证明其适用于 embodied agents。  

[Open Question] 在本节中，作者尚未证明 token / parametric / latent 三分法是否足以覆盖 object-centric、3D spatial map、multimodal episode 等具身表示；后续 §3 和 §7.4 需要逐页核验。

## Batch QA Record

- Translation QA: source paragraphs in Abstract and §1 are retained in order; citations remain in English form and are not translated.
- Figure QA: Figure 1 was checked on rendered source PDF p. 4; original caption, Chinese caption, a non-pipeline walkthrough, and grayscale guidance are recorded.
- Table QA: no table belongs to B01.
- Formula QA: no formula belongs to B01; the p. 6 equation and §2 are deliberately not extracted into this batch.
- Layout status: this is the authoritative bilingual working content. DOCX native styles, automatic TOC, original figure insertion, final pagination, and black-and-white PDF QA occur only after all P01 batches are consolidated.
