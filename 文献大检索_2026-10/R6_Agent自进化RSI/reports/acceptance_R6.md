# R6 轮验收（ROUND_DONE=True）

- 验收时间: 2026-10-01T06:01:34

| 检查项 | 结果 | 说明 |
|---|---|---|
| query_log_rows | PASS | rows=14 |
| all_queries_attempted | PASS | missing=[] |
| unique_after_dedup | PASS | unique=4352 target>=1000 |
| dedup_done | PASS |  |
| abstract_screened_advisory_1000 | PASS | L2+=508 (advisory>=1000, 若不足在漏斗中如实报告) |
| stats_done | PASS |  |
| stats_regen_possible | PASS | parquet rows=4352 |
| reading_cards_l34 | PASS | L3+L4=80 target>=60 |
| cards_on_disk | PASS | cards=80 |
| collision_check_done | PASS |  |
| report_00_检索方案与记录.md | PASS | size=13502 |
| report_01_文献地图与技术演进.md | PASS | size=11911 |
| report_02_创新点分析.md | PASS | size=11778 |
| report_03_研究空白与机会.md | PASS | size=15001 |
| report_04_论文写作建议.md | PASS | size=7741 |
| report_05_精读论文卡片集.md | PASS | size=20679 |
| funnel_report | PASS |  |
| state_updated | PASS |  |
| no_unlogged_fatal | PASS | fatal=0 |