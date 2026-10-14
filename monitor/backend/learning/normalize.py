from datetime import datetime, timezone


def received_time(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if not isinstance(result, datetime) or result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("시간대가 있는 DB 수신시각이 필요합니다.")
    return result.astimezone(timezone.utc)


def normalize_event(original):
    if type(original.get("id")) is not int or original["id"] <= 0:
        raise ValueError("원본 DB의 양수 숫자 ID가 필요합니다.")
    received_time(original["occurred_at"])
    event = dict(original)
    event.update(id=f"http-{original['id']}", source="http_live", kind=original["event_type"])
    return event
