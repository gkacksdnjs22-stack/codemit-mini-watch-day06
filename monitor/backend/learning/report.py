from learning.http_rules import find_following_errors, select_views
from learning.normalize import normalize_event


def build_report(originals, threshold=10):
    if type(threshold) is not int or not 1 <= threshold <= 100000:
        raise ValueError("기준은 1~100000 사이 정수여야 합니다.")
    events = [normalize_event(row) for row in originals]
    views = select_views(events)
    errors = find_following_errors(events, views)
    records = views + errors
    count = len(views)
    matched = count >= threshold
    card = {
        "id": "http-post-list", "title": "HTTP 목록 조회", "source": "http_live",
        "observed": count, "threshold": threshold, "matched": matched,
        "verdict": "검토 후보" if matched else "기준 미해당",
        "reason": f"목록 조회 {count}회 {'≥' if matched else '<'} 기준 {threshold}회. 뒤따른 404 {len(errors)}행은 조회 횟수에 포함하지 않습니다.",
        "view_ids": [row["id"] for row in views],
        "following_error_ids": [row["id"] for row in errors],
        "records": records, "evidence": [row["id"] for row in records],
    }
    return {"cards": [card], "limitations": "같은 서비스에서 시간상 뒤따른 기록입니다. 사용자·IP·인과관계·침해를 확정할 수 없으며, 기준 미해당은 정상 입증이 아닙니다."}
