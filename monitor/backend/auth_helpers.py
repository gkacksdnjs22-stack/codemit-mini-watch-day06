import hmac
import os
import secrets

from flask import request, session
from repositories.users import find_user_by_id


def configure_session(app):
    key = os.getenv("SECRET_KEY", "")
    if len(key) < 32 or key.startswith("GENERATE_"):
        raise RuntimeError("monitor/backend/.env에 일반 서비스와 같은 SECRET_KEY를 설정해 주세요.")
    # 같은 로컬 서비스 묶음의 게시판과 대시보드가 하나의 로그인/로그아웃을 공유합니다.
    app.config.update(SECRET_KEY=key, SESSION_COOKIE_NAME="day06_monitor_session",
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


def current_user():
    user_id = session.get("user_id")
    if session.get("role") != "operator" or type(user_id) is not int:
        return None
    user = find_user_by_id(user_id)
    if user is None:
        session.clear()
        return None
    return {"id": user["id"], "username": user["username"], "name": user["display_name"]}


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def valid_csrf():
    token, expected = request.headers.get("X-CSRF-Token"), session.get("csrf_token")
    return isinstance(token, str) and isinstance(expected, str) and hmac.compare_digest(token, expected)


def api_access_error():
    if current_user() is None:
        return {"error": "운영자 로그인이 필요합니다."}, 401
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and not valid_csrf():
        return {"error": "요청 확인 값이 만료되었습니다. 새로고침 후 다시 시도해 주세요."}, 403
    return None
