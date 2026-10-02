#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from importlib import metadata
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
packages = {}
for name in ("torch", "transformers", "vllm", "openai", "huggingface_hub"):
    try:
        packages[name] = metadata.version(name)
    except metadata.PackageNotFoundError:
        packages[name] = None

def run(command):
    return subprocess.check_output(command, cwd=ROOT, text=True).strip()

payload = {
    "python": sys.version,
    "commit": run(["git", "rev-parse", "HEAD"]),
    "dirty_files": run(["git", "status", "--short"]).splitlines(),
    "gpu_visibility": os.environ.get("CUDA_VISIBLE_DEVICES"),
    "packages": packages,
    "cuda": {
        "available": torch.cuda.is_available(),
        "visible_device_count": torch.cuda.device_count(),
        "torch_cuda_version": torch.version.cuda,
        "peer_access_0_to_1": torch.cuda.can_device_access_peer(0, 1) if torch.cuda.device_count() > 1 else None,
        "peer_access_1_to_0": torch.cuda.can_device_access_peer(1, 0) if torch.cuda.device_count() > 1 else None,
    },
}
artifacts = ROOT / "artifacts_manifest.json"
if artifacts.exists():
    payload["artifacts"] = json.loads(artifacts.read_text(encoding="utf-8"))
print(json.dumps(payload, indent=2))
