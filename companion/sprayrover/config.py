"""Loading of the shared rover configuration (``shared/config/rover.yaml``)."""

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "shared" / "config" / "rover.yaml"


def load_rover_config(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Return the rover configuration as a dictionary."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
