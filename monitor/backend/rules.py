from event_rules import make_event  # 기존 실습 import와 호환하며 분류 구현은 한 곳에 둔다.

NOTE_STATUSES = {"pending", "in_progress", "completed"}


def validate_note(data, default_status="pending"):
    if not isinstance(data, dict):
        return None, "제목과 내용을 JSON으로 보내 주세요."
    title, body = data.get("title"), data.get("body")
    if not isinstance(title, str) or not isinstance(body, str):
        return None, "제목과 내용을 문자열로 입력해 주세요."
    title, body = title.strip(), body.strip()
    if not title or not body:
        return None, "제목과 내용을 모두 입력해 주세요. 공백만 입력할 수 없습니다."
    if len(title) > 200 or len(body) > 10000:
        return None, "제목은 200자, 내용은 10,000자 이내로 입력해 주세요."
    status = data.get("status", default_status)
    if not isinstance(status, str) or status not in NOTE_STATUSES:
        return None, "처리 상태는 확인 전, 확인 중, 완료 중에서 선택해 주세요."
    return {"title": title, "body": body, "status": status}, None
