#!/usr/bin/env python3
"""Download only artifacts needed for Control evaluation and record revisions."""
import argparse
import json
import os
import tarfile
from pathlib import Path

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from huggingface_hub import HfApi, hf_hub_download, snapshot_download

ROOT = Path(__file__).resolve().parents[2]
DATASET = "ByteDance-Seed/M3-Bench"
MODEL = "ByteDance-Seed/M3-Agent-Control"

def safe_extract(archive: Path, destination: Path) -> None:
    with tarfile.open(archive, "r:gz") as tf:
        destination = destination.resolve()
        for member in tf.getmembers():
            target = (destination / member.name).resolve()
            if destination not in target.parents and target != destination:
                raise RuntimeError(f"Unsafe archive member: {member.name}")
        tf.extractall(destination)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("robot", "web", "both"), required=True)
    parser.add_argument("--download-model", action="store_true")
    parser.add_argument("--revision", default="main")
    args = parser.parse_args()
    api = HfApi()
    target = ROOT / "artifacts_manifest.json"
    if target.is_file():
        manifest = json.loads(target.read_text(encoding="utf-8"))
    else:
        manifest = {}
    manifest["dataset"] = api.dataset_info(DATASET, revision=args.revision).sha
    splits = ("robot", "web") if args.split == "both" else (args.split,)
    for split in splits:
        filename = f"memory_graphs/{split}.tar.gz"
        archive = Path(hf_hub_download(DATASET, filename, repo_type="dataset", revision=args.revision))
        safe_extract(archive, ROOT / "data" / "memory_graphs")
        manifest[f"memory_graphs_{split}"] = {
            "source": filename,
            "dataset_revision": manifest["dataset"],
        }
    if args.download_model:
        snapshot_download(MODEL, revision=args.revision, local_dir=ROOT / "models" / "M3-Agent-Control")
        manifest["control_model"] = api.model_info(MODEL, revision=args.revision).sha
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {target}")

if __name__ == "__main__":
    main()
