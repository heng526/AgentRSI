#!/usr/bin/env bash
set -euo pipefail
umask 077
root=/home/hust/research_recuris/Recuris
cd "$root"
set -a
source /home/hust/.config/m3-agent/bigmodel.env
set +a
export OPENAI_API_KEY="$GLM_API_KEY"
export OPENAI_BASE_URL="$GLM_API_BASE_URL"
export PYTHONPATH="$root/external/SkillFlow"
export PATH="$root/.venv/bin:$PATH"
conf=configs/skillflow/generated_glm_envfix
harbor run -c "$conf/bare_production-capacity-planning.yaml" --yes
harbor run -c "$conf/skill_production-capacity-planning.yaml" --yes
recuris skillflow score --bare jobs/bare_envfix --skill jobs/skill_envfix --json > /home/hust/research_recuris/skillflow_pair_score_envfix.json
