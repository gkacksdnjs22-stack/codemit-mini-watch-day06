import json
from pathlib import Path
from learning.normalize import received_time
from repositories.events import latest_event_id, read_observation

DATA_FILE = Path(__file__).parent / "data" / "observation.json"


def load_observation():
    with DATA_FILE.open(encoding="utf-8-sig") as stream:
        return json.load(stream)["records"]


def start_observation():
    return latest_event_id()


def read_live(after_id, reference_time):
    return read_observation(after_id, received_time(reference_time))
