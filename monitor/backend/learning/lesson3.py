import json
from learning.normalize import normalize_event
from learning.http_rules import select_views
from learning.support import load_observation

if __name__ == "__main__":
    rows = select_views([normalize_event(row) for row in load_observation()])
    print(json.dumps({"view_count": len(rows), "view_ids": [row["id"] for row in rows]}, ensure_ascii=False, indent=2))
