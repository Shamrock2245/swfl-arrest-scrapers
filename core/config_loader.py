"""
Configuration loader — merges global defaults, county defaults, per-county overrides, and env vars.

Priority (highest first):
    1. Environment variables
    2. config/counties/{county_name}.yaml
    3. config/counties/_defaults.yaml
    4. config/global.yaml

Usage:
    from core.config_loader import load_config
    config = load_config("charlotte")
"""

import os
import json
import yaml
from pathlib import Path
from core.exceptions import ConfigError


# Resolve paths relative to repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "config"
COUNTIES_DIR = CONFIG_DIR / "counties"


def _load_yaml(path: Path) -> dict:
    """Load a YAML file, returning empty dict if not found."""
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dicts. Override values take precedence."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(county_name: str) -> dict:
    """
    Load merged configuration for a county.

    Args:
        county_name: Lowercase county name (e.g., "charlotte", "palm_beach")

    Returns:
        Dict with all config values, merged in priority order.

    Raises:
        ConfigError: If county config file is not found.
    """
    # 1. Global defaults
    global_config = _load_yaml(CONFIG_DIR / "global.yaml")

    # 2. County defaults
    county_defaults = _load_yaml(COUNTIES_DIR / "_defaults.yaml")

    # 3. Per-county overrides
    county_file = COUNTIES_DIR / f"{county_name}.yaml"
    if not county_file.exists():
        raise ConfigError(
            f"County config not found: {county_file}. "
            f"Create it from config/counties/_defaults.yaml."
        )
    county_config = _load_yaml(county_file)

    # Merge: global → county defaults → county-specific
    merged = _deep_merge(global_config, county_defaults)
    merged = _deep_merge(merged, county_config)

    # 4. Environment variable overrides
    env_overrides = {
        "GOOGLE_SHEETS_ID": "sheets_id",
        "GOOGLE_SERVICE_ACCOUNT_KEY_PATH": "credentials_path",
        "SLACK_WEBHOOK_URL": "slack_webhook_url",
        "MONGO_URI": "mongo_uri",
        "PROXY_URL": "proxy_url",
    }
    for env_key, config_key in env_overrides.items():
        value = os.getenv(env_key)
        if value:
            merged[config_key] = value

    # Ensure required fields
    if "name" not in merged:
        merged["name"] = county_name.replace("_", " ").title()
    if "code" not in merged:
        merged["code"] = county_name.upper()

    return merged


def load_schema() -> dict:
    """Load the canonical 34-column schema."""
    schema_path = CONFIG_DIR / "schema.json"
    if not schema_path.exists():
        raise ConfigError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return json.load(f)


def load_field_aliases() -> dict:
    """Load field alias mappings."""
    aliases_path = CONFIG_DIR / "field_aliases.json"
    if not aliases_path.exists():
        raise ConfigError(f"Field aliases file not found: {aliases_path}")
    with open(aliases_path, "r") as f:
        return json.load(f)


def get_active_counties() -> list[str]:
    """Return list of county names that have enabled: true in their config."""
    active = []
    for yaml_file in sorted(COUNTIES_DIR.glob("*.yaml")):
        if yaml_file.name.startswith("_"):
            continue
        config = _load_yaml(yaml_file)
        if config.get("enabled", True):
            active.append(yaml_file.stem)
    return active
