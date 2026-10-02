# Seven-Paper Bilingual Reading Project Tracker

## Project rules in force

- Translation is paragraph-aligned: English original followed immediately by faithful Chinese translation.
- Source evidence, translation, inference, analysis, and unresolved questions remain visibly separate.
- Final deliverables for every paper are an A4 DOCX reading edition and a black-and-white-print QA PDF; these are generated only after all content batches for that paper pass consolidation QA.
- References are retained for citation lookup but are not translated paragraph by paragraph. Appendices with method, implementation, prompt, hyperparameter, ablation, or failure-analysis value are included.
- Current source set is the seven PDFs listed below. The two older project-source PDFs and the duplicate Survey copy are retained as context/source backups and are not assigned a new Paper ID.

## Document intake

| ID | Paper | Type / stated venue | Pages | Structure and reading risk | Figure / Table / equation intake | Planned priority |
|---|---|---:|---:|---|---|---|
| P01 | *Memory in the Age of AI Agents: A Survey — Forms, Functions and Dynamics* | Survey; arXiv:2512.13564v2 (2026-01-13) | 77 | Clear selectable two-column text; long taxonomy survey. No scan evidence. | ≈11 numbered figures, ≈9 numbered tables; formal equations begin in §2; Figure 1 is color-rich and needs a grayscale guide. | Foundation / first |
| P02 | *Optimus-1: Hybrid Multimodal Memory Empowered Agents Excel in Long-Horizon Tasks* | Research paper; NeurIPS 2024 stated in file name | 33 | Clear two-column text; method, tables, and a long appendix. | ≈13 figures, ≈16 tables; multiple method formulas and pseudo-code/appendix tables. | Representative hybrid multimodal memory |
| P03 | *MrSteve: Instruction-Following Agents in Minecraft with What-Where-When Memory* | Research paper; ICLR 2025 stated in PDF | 39 | Clear two-column text; extensive appendices (algorithm, environment, ablations, PEM investigation). | ≈18 figures, ≈11 tables; moderate formula/algorithm density. | Representative spatial-event episodic memory |
| P04 | *3DLLM-Mem: Long-Term Spatial-Temporal Memory for Embodied 3D Large Language Model* | Research paper; NeurIPS 2025 stated in file name | 29 | Clear text layer; PDF renderer reports singular shading-pattern warnings, so visual export needs special QA. | ≈6 figures, ≈7 tables; benchmark and memory-method equations. | Representative spatial-temporal 3D memory |
| P05 | *KARMA: Augmenting Embodied AI Agents with Long-and-short Term Memory Systems* | Research paper; venue not established by supplied PDF | 19 | Text is extractable but every page contains raster objects; final figures/tables need resolution review. | ≈1 figure, ≈4 tables; low–moderate equation density. | Long-/short-term scene-graph memory |
| P06 | *Embodied VideoAgent: Persistent Memory from Egocentric Videos and Embodied Sensors Enables Dynamic Scene Understanding* | Research paper; arXiv:2501.00358v2 | 29 | Clear text layer, many high-resolution embedded visual assets. | ≈15 figures, ≈4 tables; algorithmic 3D object-memory updates. | Dynamic multimodal scene memory |
| P07 | *Seeing, Listening, Remembering, and Reasoning: A Multimodal Agent with Long-Term Memory* (M3-Agent) | Research paper; arXiv:2508.09736v4 | 48 | Clear text layer; long dataset/evaluation appendix and table-heavy content. | ≈4 figures, ≈22 tables; moderate memory/learning formulas. | Entity-centric audio-visual long-term memory |

### Global source quality findings

- No source appears to be a scanned-only PDF; all seven expose an extractable text layer.
- Every source is multi-column or visually complex enough that final translation alignment is checked against rendered PDF pages, not text extraction alone.
- P04 requires an additional renderer-compatibility check before final PDF release. P05 needs image-resolution checking because its source pages contain raster image objects throughout.
- Deduplication: `Memory in the Age of AI Agents A Survey_1-77.pdf` is the P01 source. The similarly named file in `project_sources/` is a prior duplicate/backup and is not translated twice.

## Processing order

P01 Survey → P02 Optimus-1 → P03 MrSteve → P04 3DLLM-Mem → P05 KARMA → P06 Embodied VideoAgent → P07 M3-Agent.

This order first establishes a common definition/taxonomy, then covers four especially relevant embodied-memory mechanisms before the two current preprints with dynamic scene and multimodal episodic memory.

## P01 batch plan — *Memory in the Age of AI Agents: A Survey*

| Batch | Source scope / complete section boundary | Primary content | Status |
|---|---|---|---|
| B01 | PDF pp. 1–5 plus the Introduction closing text at the top of p. 6 | Paper information, abstract, contents, Figure 1, §1 Introduction | **COMPLETED** |
| B02 | PDF pp. 6–11, excluding the already-recorded §1 closing text | §2 and §§2.1–2.3.3 | Pending |
| B03 | PDF pp. 12–21 | §3.1 and §§3.1.1–3.1.3 | Pending |
| B04 | PDF pp. 22–30 | §§3.2–3.4 | Pending |
| B05 | PDF pp. 31–36 | §4.1 and §§4.1.1–4.1.2 | Pending |
| B06 | PDF pp. 37–45 | §§4.2–4.3 and their subtypes | Pending |
| B07 | PDF pp. 46–54 | §5.1 and formation subtypes | Pending |
| B08 | PDF pp. 55–64 | §§5.2–5.3 and evolution/retrieval subtypes | Pending |
| B09 | PDF pp. 65–68 | §6 resources and frameworks | Pending |
| B10 | PDF pp. 69–76 | §7 frontiers and §8 conclusion | Pending |
| Final QA | PDF p. 77 references plus whole-paper consolidation | Terminology, citations, figures/tables/equations, pagination, DOCX/PDF/grayscale QA | Pending |

## Paper status

| Field | P01 current value |
|---|---|
| Paper ID / title | P01 / *Memory in the Age of AI Agents: A Survey — Forms, Functions and Dynamics* |
| Total pages | 77 |
| Current batch | B01 complete; next B02 |
| Completed pages | PDF pp. 1–5; §1 closing text on p. 6 captured. p. 6 is not counted as fully complete because §2 begins on it. |
| Completed sections | Abstract; §1 Introduction |
| Pending sections | §2–§8; selected method-relevant appendix content if found; references retained but not translated |
| Figure status | Figure 1 source page visually checked; original caption, Chinese caption, walkthrough, and grayscale-reading instruction captured |
| Table status | No table occurs in B01 |
| Equation status | No equation belongs to B01. The equation at p. 6 belongs to B02 and is deferred intact. |
| Glossary status | Initial P01 glossary entries added in B01 |
| DOCX / PDF status | Not generated yet; generated after P01 full-content consolidation |
| QA status | B01 source-text alignment and Figure 1 visual check completed; full-paper QA pending |

## Unresolved source issues

| Paper | Location | Issue / handling |
|---|---|---|
| P01 | §1, p. 4 | The source spells “interlligence” in “artificial general interlligence.” The English original is preserved as printed; Chinese translates the intended term “artificial general intelligence.” |
| P04 | Source PDF rendering | Singular shading-pattern warnings were emitted while inspecting image resources. Text is intact; final visual PDF export will be rendered page by page and checked before delivery. |
| P05 | Whole source | Raster objects occur on all pages; source figure/table resolution will be verified at final A4 placement rather than artificially enlarged. |

## Master glossary seed

The live, paper-specific glossary begins in the B01 working file. Cross-paper unification is deferred until all papers are processed, so paper-specific author definitions are not overwritten.
