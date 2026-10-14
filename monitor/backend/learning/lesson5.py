import json
from learning.normalize import normalize_event
from learning.http_rules import find_following_errors, select_views
from learning.support import load_observation

if __name__ == "__main__":
    events = [normalize_event(row) for row in load_observation()]
    views = select_views(events)
    print(json.dumps({"view_count": len(views), "following_errors": find_following_errors(events, views)}, ensure_ascii=False, indent=2))
