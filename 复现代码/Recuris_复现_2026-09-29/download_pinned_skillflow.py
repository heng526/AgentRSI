#!/usr/bin/env python3
"""Download selected SkillFlow families at one immutable dataset revision."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

import requests

DATASET = "zhang-ziao/SkillFlow-Task"
REVISION = "ecaadb0e25d5d5cfd87bd86d81e77b4abe3a00bc"
MIRROR = "https://hf-mirror.com"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_one(entry: dict, destination: Path) -> dict:
    relative = entry["path"]
    target = destination / relative
    size = entry["size"]
    if not target.is_file() or target.stat().st_size != size:
        target.parent.mkdir(parents=True, exist_ok=True)
        url = f"{MIRROR}/datasets/{DATASET}/resolve/{REVISION}/{quote(relative, safe='/')}"
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                if len(response.content) != size:
                    raise ValueError(f"wrong size for {relative}")
                target.write_bytes(response.content)
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))
    return {"path": relative, "size": size, "sha256": sha256(target)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    parser.add_argument("family", nargs="+")
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=True)
    manifest = {"dataset": DATASET, "revision": REVISION, "families": {}}
    for family in args.family:
        url = f"{MIRROR}/api/datasets/{DATASET}/tree/{REVISION}/test_tasks/{quote(family)}"
        response = requests.get(url, params={"recursive": "true", "limit": 1000}, timeout=60)
        response.raise_for_status()
        entries = response.json()
        if len(entries) >= 1000:
            raise RuntimeError(f"pagination required for {family}")
        files = [
            entry for entry in entries
            if entry.get("type") == "file" and not entry["path"].endswith("/.DS_Store")
        ]
        with ThreadPoolExecutor(max_workers=6) as executor:
            records = sorted(executor.map(lambda e: download_one(e, args.destination), files), key=lambda x: x["path"])
        task_root = args.destination / "test_tasks" / family
        tasks = sorted(path.parent.name for path in task_root.rglob("task.toml"))
        if not tasks:
            raise RuntimeError(f"no task.toml files under {task_root}")
        manifest["families"][family] = {"tasks": tasks, "files": records}
        print(f"{family}: {len(tasks)} tasks, {len(records)} files", flush=True)
    output = args.destination.parent / "dataset_manifest.json"
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
