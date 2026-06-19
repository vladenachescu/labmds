from pathlib import Path
from typing import Any

import yaml


DEFAULT_DB_PATH = Path.cwd() / "rssmds.db"

DEFAULT_CONFIG: dict[str, Any] = {
    "db_path": str(DEFAULT_DB_PATH),
    "fetch_timeout": 15,
    "max_entries_per_list": 50,
}


def load_config(path: str | None = None) -> dict[str, Any]:
    config = DEFAULT_CONFIG.copy()

    if path is None:
        path = str(Path.home() / ".rssmds" / "config.yml")

    p = Path(path)
    if not p.exists():
        return config

    with open(p) as f:
        user_config: dict[str, Any] = yaml.safe_load(f) or {}

    for key, value in user_config.items():
        if key in config:
            config[key] = value

    return config
