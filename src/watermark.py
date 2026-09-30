import json
from pathlib import Path


STATE_PATH = Path("data/state/watermarks.json")


def load_watermark(entity):
    if not STATE_PATH.exists():
        return None

    with STATE_PATH.open("r", encoding="utf-8") as file:
        state = json.load(file)

    return state.get(entity)


def save_watermark(entity, watermark):
    STATE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    state = {}

    if STATE_PATH.exists():
        with STATE_PATH.open("r", encoding="utf-8") as file:
            state = json.load(file)

    state[entity] = watermark

    with STATE_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            state,
            file,
            indent=2
        )