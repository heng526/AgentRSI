# AgentRSI

AgentRSI is the canonical P0 GitHub repository for the CVPR-RSI research project. It keeps project code, papers, configurations, and research records together while leaving datasets, model weights, temporary outputs, and credentials out of Git.

## Project materials

- `翻译/` — paper translations and related source papers.
- `复现代码/` — reproduction code, experiment configurations, protocols, and run records.
- `解读笔记/` — paper reading notes and research analysis.
- `提取文本/` — retained text extracts used in research notes.
- `文献大检索_2026-10/` — literature-search reports and reading cards. Raw retrieval payloads and bulky full-text caches stay local.
- `文献PDF/` — selected source papers.
- `researchops/` — canonical task, decision, result, state, and ledger protocol.

## ResearchOps

Use the existing `research-dual-agent-orchestrator` contract. The machine bus is the append-only `researchops/outbox/{gpt,codex,human}/` records, with reducer-owned state and ledger files. Do not create a parallel task board or edit reducer-generated state by hand.

Validate the repository with:

```powershell
python path\to\research-dual-agent-orchestrator\scripts\validate_researchops.py --repo-root .
```

## Repository hygiene

The root `.gitignore` excludes secrets, datasets, model checkpoints, run/output folders, caches, and temporary logs. Add individual, reviewed JSON/CSV research evidence explicitly when it is needed; do not track an entire generated output directory.
