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


def make_event(data):
    if not isinstance(data, dict):
        return None
    method, path, status = data.get("method"), data.get("path"), data.get("status_code")
    if not isinstance(method, str) or method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
        return None
    if not isinstance(path, str) or not path.startswith("/") or len(path) > 500:
        return None
    if type(status) is not int or not 100 <= status <= 599:
        return None
    if method == "POST" and path in {"/auth/login", "/login", "/api/auth/login"} and status in (200, 303, 401):
        event_type = "login_success" if status in (200, 303) else "login_failure"
    else:
        event_type = "http_request"
    return {"method": method, "path": path, "status_code": status, "event_type": event_type}
