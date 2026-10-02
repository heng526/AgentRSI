#!/usr/bin/env python3
"""Render the upstream Azure config without printing credential material."""
import json
import os
import stat
import sys
from pathlib import Path
from typing import Optional

from dotenv import dotenv_values

env_file = Path(os.environ.get("M3_AZURE_ENV_FILE", Path.home() / ".config" / "m3-agent" / "azure.env"))
file_values = dotenv_values(env_file) if env_file.is_file() else {}

def value(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(name) or file_values.get(name) or default

required = ("AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT")
missing = [name for name in required if not value(name)]
if missing:
    raise SystemExit("Missing required environment variable(s): " + ", ".join(missing))

deployment = value("M3_AZURE_DEPLOYMENT", "gpt-4o-2024-11-20")
payload = {
    deployment: {
        "azure_endpoint": value("AZURE_OPENAI_ENDPOINT"),
        "api_version": value("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        "api_key": value("AZURE_OPENAI_API_KEY"),
    }
}
target = Path(__file__).resolve().parents[2] / "configs" / "api_config.json"
target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
target.chmod(stat.S_IRUSR | stat.S_IWUSR)
print(f"Wrote protected Azure configuration for deployment: {deployment}")
