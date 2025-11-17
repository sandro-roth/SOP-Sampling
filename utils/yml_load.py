import os
from pathlib import Path

import yaml

def load_yaml(path: Path | None = None) -> yaml:
    with open ((path or Path(os.getenv('CONFIG_DIR'),  'statements.yml')), 'r') as file:
        return yaml.safe_load(file)