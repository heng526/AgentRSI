#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONDA_ROOT="${CONDA_ROOT:-/home/hust/miniconda3}"
ENV_NAME="${M3_CONDA_ENV:-m3-agent-repro}"
PIP_INDEX_URL="${M3_PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"

source "${CONDA_ROOT}/etc/profile.d/conda.sh"
conda activate "${ENV_NAME}"

python -m pip install --index-url "${PIP_INDEX_URL}" --upgrade pip
python -m pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 \
  --index-url "${PIP_INDEX_URL}"
python -m pip install --index-url "${PIP_INDEX_URL}" -r "${ROOT}/requirements.txt"
# vLLM 0.8.4's current package metadata asks for transformers>=4.51.1,
# while the upstream M3-Agent README explicitly pins 4.51.0. Install vLLM's
# dependency set first, then restore the paper's pinned transformer without
# allowing pip to silently choose a different version.
python -m pip install vllm==0.8.4 'huggingface_hub[cli]>=0.29,<1' \
  --index-url "${PIP_INDEX_URL}"
python -m pip install --no-deps transformers==4.51.0 tokenizers==0.21.4 numpy==1.26.4 \
  --index-url "${PIP_INDEX_URL}"
python - <<'PY'
import importlib.metadata as md
for package in ("torch", "transformers", "vllm", "openai", "huggingface_hub"):
    print(f"{package}={md.version(package)}")
PY
