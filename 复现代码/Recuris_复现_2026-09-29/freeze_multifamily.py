#!/usr/bin/env python3
"""Record the exact Recuris/SkillFlow treatment and container identities."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/hust/research_recuris/Recuris")
OUTPUT = Path("/home/hust/research_recuris/frozen/multifamily_manifest.json")
FAMILIES = ("Production-Capacity-Planning", "Cross-Format-Data-Reconciliation")


def command(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(bytes.fromhex(file_hash(path)))
    return digest.hexdigest()


def image_id(tag: str) -> str:
    return command("docker", "image", "inspect", tag, "--format", "{{.Id}}")


def main() -> None:
    dataset = json.loads((ROOT / "external/SkillFlow/dataset_manifest.json").read_text())
    config_root = ROOT / "configs/skillflow/generated_k2"
    tasks_root = ROOT / "external/SkillFlow/test_tasks/test_tasks"
    tasks: dict[str, dict[str, str]] = {}
    for family in FAMILIES:
        expected = set(dataset["families"][family]["tasks"])
        actual = {p.parent.name for p in (tasks_root / family).rglob("task.toml")}
        if expected != actual:
            raise RuntimeError(f"task list changed in {family}")
        tasks[family] = {}
        for task in sorted(actual):
            task_dir = tasks_root / family / task
            text = (task_dir / "task.toml").read_text()
            image = next(
                line.split("=", 1)[1].strip().strip('"').strip("'")
                for line in text.splitlines() if line.strip().startswith("docker_image =")
            )
            tasks[family][task] = image_id(image)
    configs = {path.name: file_hash(path) for path in sorted(config_root.glob("*.yaml"))}
    patch = command("git", "diff", "--binary")
    key_values = {}
    for line in Path("/home/hust/.config/m3-agent/bigmodel.env").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            name, value = line.split("=", 1)
            if name in ("GLM_CHAT_MODEL", "GLM_API_BASE_URL"):
                key_values[name] = value.strip().strip('"').strip("'")
    base_archive = Path("/home/hust/research_recuris/frozen/skillflow-base-qwen0.24.6.tar.zst")
    mirror_archive = Path("/home/hust/research_recuris/frozen/skillflow-base-pip-tuna.tar.zst")
    task_archive = Path("/home/hust/research_recuris/frozen/skillflow-task-images-k2.tar.zst")
    output = {
        "recuris_commit": command("git", "rev-parse", "HEAD"),
        "local_source_patch_sha256": hashlib.sha256(patch.encode()).hexdigest(),
        "uv_lock_sha256": file_hash(ROOT / "uv.lock"),
        "python": sys.version.split()[0],
        "harbor": command(str(ROOT / ".venv/bin/python"), "-c", "import importlib.metadata as m; print(m.version('harbor'))"),
        "skillflow_source_commit": (ROOT / "third_party/skillflow/upstream.commit").read_text().strip(),
        "skillflow_dataset_revision": dataset["revision"],
        "dataset_manifest_sha256": file_hash(ROOT / "external/SkillFlow/dataset_manifest.json"),
        "skill_memory_tree_sha256": tree_hash(ROOT / "skill_memories/skillflow"),
        "model": key_values["GLM_CHAT_MODEL"],
        "api_base_url": key_values["GLM_API_BASE_URL"],
        "qwen_code_version": command("docker", "run", "--rm", "--entrypoint", "qwen", "skillflow/harbor-cli-base:ubuntu24.04", "--version"),
        "docker_server": command("docker", "info", "--format", "{{.ServerVersion}}"),
        "docker_compose": command("docker", "compose", "version", "--short"),
        "ubuntu_image_id": image_id("ubuntu:24.04"),
        "skillflow_base_image_id": image_id("skillflow/harbor-cli-base:ubuntu24.04"),
        "base_image_archive_sha256": file_hash(base_archive),
        "crossformat_build_base_image_id": image_id("skillevlove/harbor-cli-openhands:ubuntu24.04"),
        "crossformat_build_base_archive_sha256": file_hash(mirror_archive),
        "pip_mirror_dockerfile_sha256": file_hash(Path("/home/hust/research_recuris/frozen/Dockerfile.pip-mirror")),
        "task_image_archive_sha256": file_hash(task_archive),
        "task_image_archive_bytes": task_archive.stat().st_size,
        "configs_sha256": configs,
        "task_image_ids": tasks,
        "replicates_per_task_per_arm": 2,
        "harbor_attempts_per_trial": 1,
        "harbor_concurrent_trials": 3,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
