import hmac
import os
import secrets

from flask import request, session
from repositories.users import find_user_by_id


def configure_session(app):
    key = os.getenv("SECRET_KEY", "")
    if len(key) < 32 or key.startswith("GENERATE_"):
        raise RuntimeError("general/.env에 32자 이상의 SECRET_KEY를 설정해 주세요.")
    app.config.update(SECRET_KEY=key, SESSION_COOKIE_NAME="day06_general_session",
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


def current_user():
    user_id = session.get("user_id")
    if type(user_id) is not int:
        return None
    if session.get("role") == "operator":
        return {"id": user_id, "username": session.get("username"), "name": session.get("name"), "role": "operator"}
    if session.get("role") != "member":
        return None
    user = find_user_by_id(user_id)
    if user is None:
        session.clear()
        return None
    return {"id": user["id"], "username": user["username"], "name": user["display_name"], "role": "member"}


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def valid_csrf():
    token, expected = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token"), session.get("csrf_token")
    return isinstance(token, str) and isinstance(expected, str) and hmac.compare_digest(token, expected)


def template_auth():
    return {"login_user": current_user(), "csrf_token": csrf_token,
            "dashboard_url": os.getenv("DASHBOARD_URL", "http://127.0.0.1:5173/")}
