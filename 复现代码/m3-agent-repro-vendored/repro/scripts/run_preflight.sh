#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MODE="${1:-local}"
SPLIT="${2:-robot}"
case "${MODE}" in local|azure|glm) ;; *) echo "Usage: run_preflight.sh [local|azure|glm] [robot|web]" >&2; exit 2;; esac
case "${SPLIT}" in robot|web) ;; *) echo "Invalid split: ${SPLIT}" >&2; exit 2;; esac
source /home/hust/miniconda3/etc/profile.d/conda.sh
conda activate "${M3_CONDA_ENV:-m3-agent-repro}"
cd "${ROOT}"
export CUDA_VISIBLE_DEVICES="${M3_GPUS:-0,1}"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

nvidia-smi --query-gpu=index,name,memory.total,memory.used,driver_version --format=csv,noheader
python - <<'PY'
import torch
assert torch.cuda.is_available(), "CUDA is unavailable"
assert torch.cuda.device_count() == 2, f"Expected 2 visible GPUs, found {torch.cuda.device_count()}"
p2p_01 = torch.cuda.can_device_access_peer(0, 1)
p2p_10 = torch.cuda.can_device_access_peer(1, 0)
print(f"CUDA peer access: 0->1={p2p_01}, 1->0={p2p_10}")
if not (p2p_01 and p2p_10):
    print("WARNING: CUDA P2P is unavailable; continuing only if the NCCL probe succeeds.")
PY
torchrun --standalone --nproc_per_node=2 repro/scripts/nccl_probe.py
python - <<PY
import json
import os
from pathlib import Path

root = Path("${ROOT}")
model = root / "models/M3-Agent-Control"
required = ["config.json", "tokenizer.json", "tokenizer_config.json", "model.safetensors.index.json"]
missing = [name for name in required if not (model / name).is_file()]
if missing:
    raise SystemExit("Missing Control model files: " + ", ".join(missing))
index = json.loads((model / "model.safetensors.index.json").read_text())
shards = sorted(set(index["weight_map"].values()))
absent = [name for name in shards if not (model / name).is_file()]
if absent:
    raise SystemExit("Missing Control weight shard(s): " + ", ".join(absent))
annotation_path = root / "data/annotations/${SPLIT}.json"
if not annotation_path.is_file():
    raise SystemExit(f"Missing annotations: {annotation_path}")
annotations = json.loads(annotation_path.read_text())
from repro.scripts.qa_selection import select_qa_pairs
qa_limit = os.environ.get("M3_CHECK_MAX_QAS")
selected_videos = {video_id for video_id, _ in select_qa_pairs(
    annotations, int(qa_limit) if qa_limit else None
)}
def graph_path(item):
    original = Path(item["mem_path"])
    if "${MODE}" == "glm":
        from mmagent.utils.chat_api import glm_settings
        if original.parts[:2] != ("data", "memory_graphs"):
            raise SystemExit(f"Unexpected source graph path: {original}")
        return root / "data" / f"memory_graphs_{glm_settings()['provider']}" / Path(*original.parts[2:])
    return root / original
missing_graphs = sorted({str(graph_path(annotations[video_id])) for video_id in selected_videos
                         if not graph_path(annotations[video_id]).is_file()})
if missing_graphs:
    raise SystemExit(f"{len(missing_graphs)} ${SPLIT} memory graph(s) missing; first: {missing_graphs[0]}")
print(f"Control shards: {len(shards)} present")
print(f"${SPLIT} videos: {len(annotations)}; QA pairs: {sum(len(item['qa_list']) for item in annotations.values())}; memory graphs present")
PY
if [[ "${MODE}" == "azure" ]]; then
  python repro/scripts/prepare_api_config.py
elif [[ "${MODE}" == "glm" ]]; then
  python -c 'from mmagent.utils.chat_api import glm_settings; s=glm_settings(); print("GLM API configured:", s["provider"], s["chat_model"], s["embedding_model"])'
fi
echo "Preflight passed (${MODE}, ${SPLIT})"
