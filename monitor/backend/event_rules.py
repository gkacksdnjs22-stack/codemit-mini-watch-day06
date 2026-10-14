"""수신한 실제 요청을 분류한다. 사용자나 IP를 추정하지 않는다."""


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
    if method == "GET" and path == "/" and status == 200:
        kind = "post_list"
    elif status >= 400:
        kind = "request_error"
        if method == "POST" and path in {"/auth/login", "/login", "/api/auth/login"} and status == 401:
            kind = "login_failure"
    elif method == "POST" and path in {"/auth/login", "/login", "/api/auth/login"} and status in {200, 303}:
        kind = "login_success"
    else:
        kind = "http_request"
    return {"method": method, "path": path, "status_code": status, "event_type": kind}
