#!/usr/bin/env bash
set -euo pipefail
root=/home/hust/research_recuris/Recuris
cd "$root"
export QWEN_CODE_VERSION=0.24.6
./external/SkillFlow/docker/harbor-cli-base/build.sh
actual="$(docker run --rm --entrypoint qwen skillflow/harbor-cli-base:ubuntu24.04 --version)"
test "$actual" = "0.24.6"
docker tag skillflow/harbor-cli-base:ubuntu24.04 skillflow/harbor-cli-base:qwen0.24.6-orig
