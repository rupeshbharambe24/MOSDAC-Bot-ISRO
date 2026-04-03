# Training data loader - loads from curated JSON file
# Used by graph_cleaner.py and other scripts that import TRAINING_EXAMPLES
import json
import os

_data_path = os.path.join(os.path.dirname(__file__), "training_data_curated.json")

def _load():
    with open(_data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["examples"]

TRAINING_EXAMPLES = _load()
