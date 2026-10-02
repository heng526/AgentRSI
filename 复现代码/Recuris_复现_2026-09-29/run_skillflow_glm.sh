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
docker compose version
docker info --format '{{.ServerVersion}}'
./external/SkillFlow/docker/harbor-cli-base/build.sh
python external/SkillFlow/utils/prebuild_task_images.py --tasks-root external/SkillFlow/test_tasks/test_tasks/Production-Capacity-Planning
harbor run -c configs/skillflow/generated_glm/bare_production-capacity-planning.yaml --yes
harbor run -c configs/skillflow/generated_glm/skill_production-capacity-planning.yaml --yes
recuris skillflow score --bare jobs/bare --skill jobs/skill --json > /home/hust/research_recuris/skillflow_pair_score.json
