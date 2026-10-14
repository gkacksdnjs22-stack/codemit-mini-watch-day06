from learning.normalize import received_time


def select_views(events):
    return [event for event in events if event.get("method") == "GET"
            and event.get("path") == "/" and event.get("status_code") == 200
            and event.get("kind") == "post_list"]


def find_following_errors(events, views):
    if not views:
        return []
    last_time = max(received_time(event["occurred_at"]) for event in views)
    return [event for event in events if event.get("status_code") == 404
            and 0 < (received_time(event["occurred_at"]) - last_time).total_seconds() <= 30]
