import json
from learning.normalize import normalize_event
from learning.support import load_observation

if __name__ == "__main__":
    rows = load_observation()
    normalized = [normalize_event(row) for row in rows]
    print(json.dumps({"original_count": len(rows), "normalized_count": len(normalized), "records": normalized}, ensure_ascii=False, indent=2))
