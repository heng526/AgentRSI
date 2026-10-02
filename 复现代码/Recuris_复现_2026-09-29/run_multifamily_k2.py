#!/usr/bin/env python3
"""Run two paired SkillFlow replicates per task with a frozen GLM treatment."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path("/home/hust/research_recuris/Recuris")
FROZEN = Path("/home/hust/research_recuris/frozen")
CONFIGS = ROOT / "configs/skillflow/generated_k2"
JOBS = ROOT / "jobs/multifamily_k2"
OLD = {
    "bare": ROOT / "jobs/bare_envfix/recuris-bare-envfix-production-capacity-planning",
    "skill": ROOT / "jobs/skill_envfix/recuris-skill-envfix-production-capacity-planning",
}
FAMILIES = {
    "Production-Capacity-Planning": "production-capacity-planning",
    "Cross-Format-Data-Reconciliation": "cross-format-data-reconciliation",
}
RUNS = (
    ("Cross-Format-Data-Reconciliation", 1, "bare"),
    ("Cross-Format-Data-Reconciliation", 1, "skill"),
    ("Cross-Format-Data-Reconciliation", 2, "bare"),
    ("Cross-Format-Data-Reconciliation", 2, "skill"),
    ("Production-Capacity-Planning", 2, "bare"),
    ("Production-Capacity-Planning", 2, "skill"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def shell(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def model_env(manifest: dict) -> dict[str, str]:
    values = {}
    for line in Path("/home/hust/.config/m3-agent/bigmodel.env").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            name, value = line.split("=", 1)
            values[name] = value.strip().strip('"').strip("'")
    if values.get("GLM_CHAT_MODEL") != manifest["model"]:
        raise RuntimeError("GLM model changed")
    if values.get("GLM_API_BASE_URL") != manifest["api_base_url"]:
        raise RuntimeError("GLM API base URL changed")
    if not values.get("GLM_API_KEY"):
        raise RuntimeError("GLM API key missing")
    env = os.environ.copy()
    env.update({
        "OPENAI_API_KEY": values["GLM_API_KEY"],
        "OPENAI_BASE_URL": values["GLM_API_BASE_URL"],
        "OPENAI_API_BASE": values["GLM_API_BASE_URL"],
        "PYTHONPATH": str(ROOT / "external/SkillFlow"),
        "PATH": str(ROOT / ".venv/bin") + ":" + env.get("PATH", ""),
    })
    return env


def validate_job(job: Path, expected: set[str]) -> dict[str, float]:
    if not job.is_dir():
        raise RuntimeError(f"job missing: {job}")
    rewards = {}
    for path in sorted(job.glob("*/result.json")):
        doc = json.loads(path.read_text())
        name = doc.get("task_name")
        if doc.get("exception_info") is not None:
            raise RuntimeError(f"exception in {path}")
        value = ((doc.get("verifier_result") or {}).get("rewards") or {}).get("reward")
        if not isinstance(value, (int, float)):
            raise RuntimeError(f"ungraded trial: {path}")
        if name in rewards:
            raise RuntimeError(f"duplicate task in {job}: {name}")
        rewards[name] = float(value)
    if set(rewards) != expected:
        raise RuntimeError(f"task mismatch in {job}: got {sorted(rewards)}, expected {sorted(expected)}")
    return rewards


def preflight(manifest: dict, dataset: dict) -> None:
    if shell("git", "rev-parse", "HEAD") != manifest["recuris_commit"]:
        raise RuntimeError("Recuris commit changed")
    patch = shell("git", "diff", "--binary")
    if hashlib.sha256(patch.encode()).hexdigest() != manifest["local_source_patch_sha256"]:
        raise RuntimeError("local source patch changed")
    if sha256(ROOT / "uv.lock") != manifest["uv_lock_sha256"]:
        raise RuntimeError("uv.lock changed")
    if sha256(ROOT / "external/SkillFlow/dataset_manifest.json") != manifest["dataset_manifest_sha256"]:
        raise RuntimeError("dataset manifest changed")
    if shell("docker", "image", "inspect", "skillflow/harbor-cli-base:ubuntu24.04", "--format", "{{.Id}}") != manifest["skillflow_base_image_id"]:
        raise RuntimeError("SkillFlow base image changed")
    if shell("docker", "image", "inspect", "skillevlove/harbor-cli-openhands:ubuntu24.04", "--format", "{{.Id}}") != manifest["crossformat_build_base_image_id"]:
        raise RuntimeError("Cross-Format build base image changed")
    if sha256(FROZEN / "skillflow-base-pip-tuna.tar.zst") != manifest["crossformat_build_base_archive_sha256"]:
        raise RuntimeError("Cross-Format build base archive changed")
    if sha256(FROZEN / "skillflow-task-images-k2.tar.zst") != manifest["task_image_archive_sha256"]:
        raise RuntimeError("task image archive changed")
    if shell("docker", "run", "--rm", "--entrypoint", "qwen", "skillflow/harbor-cli-base:ubuntu24.04", "--version") != manifest["qwen_code_version"]:
        raise RuntimeError("Qwen Code version changed")
    for filename, expected_hash in manifest["configs_sha256"].items():
        if sha256(CONFIGS / filename) != expected_hash:
            raise RuntimeError(f"config changed: {filename}")
    for family, slug in FAMILIES.items():
        bare = yaml.safe_load((CONFIGS / f"bare_{slug}.yaml").read_text())
        skill = yaml.safe_load((CONFIGS / f"skill_{slug}.yaml").read_text())
        for config in (bare, skill):
            if "api_key" in config["agents"][0].get("kwargs", {}):
                raise RuntimeError(f"credential placeholder in {family} config")
        for config in (bare, skill):
            config.pop("job_name", None)
            config.pop("jobs_dir", None)
            config["agents"][0]["kwargs"].pop("prompt_template_path", None)
        if bare != skill:
            raise RuntimeError(f"arm treatment drift in {family}")
    for family, task_images in manifest["task_image_ids"].items():
        if set(task_images) != set(dataset["families"][family]["tasks"]):
            raise RuntimeError(f"task split changed: {family}")
        for task, expected_id in task_images.items():
            task_toml = ROOT / "external/SkillFlow/test_tasks/test_tasks" / family / task / "task.toml"
            image = next(
                line.split("=", 1)[1].strip().strip('"').strip("'")
                for line in task_toml.read_text().splitlines()
                if line.strip().startswith("docker_image =")
            )
            if shell("docker", "image", "inspect", image, "--format", "{{.Id}}") != expected_id:
                raise RuntimeError(f"task image changed: {family}/{task}")


def main() -> None:
    manifest = json.loads((FROZEN / "multifamily_manifest.json").read_text())
    dataset = json.loads((ROOT / "external/SkillFlow/dataset_manifest.json").read_text())
    preflight(manifest, dataset)
    env = model_env(manifest)
    if "--check-only" in sys.argv[1:]:
        print("PREFLIGHT_OK", flush=True)
        return
    FROZEN.mkdir(exist_ok=True)
    logs = FROZEN / "multifamily_logs"
    logs.mkdir(exist_ok=True)
    records = []
    for arm, old_job in OLD.items():
        expected = set(dataset["families"]["Production-Capacity-Planning"]["tasks"])
        records.append({"family": "Production-Capacity-Planning", "replicate": 1, "arm": arm,
                        "job": str(old_job), "rewards": validate_job(old_job, expected)})
    for family, replicate, arm in RUNS:
        slug = FAMILIES[family]
        job_name = f"recuris-{arm}-{slug}-r{replicate}"
        job = JOBS / arm / job_name
        expected = set(dataset["families"][family]["tasks"])
        if not job.exists():
            config = CONFIGS / f"{arm}_{slug}.yaml"
            command = [str(ROOT / ".venv/bin/harbor"), "run", "-c", str(config),
                       "--job-name", job_name, "--jobs-dir", str(JOBS / arm), "--yes"]
            print(f"START {family} r{replicate} {arm}", flush=True)
            with (logs / f"{job_name}.log").open("w") as stream:
                result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
            if result.returncode:
                raise RuntimeError(f"Harbor failed: {job_name}; inspect its log")
        rewards = validate_job(job, expected)
        records.append({"family": family, "replicate": replicate, "arm": arm,
                        "job": str(job), "rewards": rewards})
        (FROZEN / "multifamily_run_state.json").write_text(json.dumps(records, indent=2) + "\n")
        print(f"DONE {family} r{replicate} {arm}: {sum(rewards.values())}/{len(rewards)}", flush=True)
    aggregate = FROZEN / "aggregate"
    for record in records:
        family = record["family"]
        replica = record["replicate"]
        arm = record["arm"]
        job = Path(record["job"])
        for source in sorted(job.glob("*/result.json")):
            doc = json.loads(source.read_text())
            destination = aggregate / arm / family / f"r{replica}" / doc["task_name"] / "result.json"
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() or destination.is_symlink():
                if destination.resolve() != source.resolve():
                    raise RuntimeError(f"aggregate collision: {destination}")
            else:
                destination.symlink_to(source.resolve())
    score = FROZEN / "multifamily_score_k2.json"
    with score.open("w") as stream:
        subprocess.run([str(ROOT / ".venv/bin/recuris"), "skillflow", "score",
                        "--bare", str(aggregate / "bare"), "--skill", str(aggregate / "skill"),
                        "--json"], cwd=ROOT, check=True, stdout=stream)
    result = json.loads(score.read_text())
    target_tasks = sum(len(dataset["families"][family]["tasks"]) for family in FAMILIES)
    for arm in ("bare", "skill"):
        if result[arm]["tasks"] != target_tasks or result[arm]["trials"] != target_tasks * 2:
            raise RuntimeError(f"incomplete aggregate for {arm}")
    print(f"SCORE {score}", flush=True)


if __name__ == "__main__":
    main()
