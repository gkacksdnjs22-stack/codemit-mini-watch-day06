import hmac
from flask import Blueprint, current_app, request, session
from werkzeug.security import check_password_hash
from repositories.users import find_user
from auth_helpers import csrf_token, current_user, valid_csrf

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.get("/me")
def me():
    return {"user": current_user(), "csrf_token": csrf_token()}


@auth_bp.post("/account-exists")
def account_exists():
    # 회원가입의 아이디 중복 확인에만 사용하는 서버 간 요청입니다.
    if not hmac.compare_digest(request.headers.get("X-Internal-Auth", ""), current_app.secret_key):
        return {"error": "허용되지 않은 요청입니다."}, 403
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("username"), str):
        return {"error": "아이디를 보내 주세요."}, 400
    return {"exists": find_user(data["username"].strip()) is not None}


@auth_bp.post("/login")
def login():
    if not valid_csrf():
        return {"error": "로그인 화면을 새로고침하고 다시 시도해 주세요."}, 403
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return {"error": "아이디와 비밀번호를 입력해 주세요."}, 400
    username, password = data.get("username"), data.get("password")
    if (not isinstance(username, str) or not isinstance(password, str)
            or not username.strip() or not password.strip()):
        return {"error": "아이디와 비밀번호를 모두 입력해 주세요."}, 400
    user = find_user(username.strip())
    if user is None or not check_password_hash(user["password_hash"], password):
        return {"error": "아이디 또는 비밀번호가 올바르지 않습니다."}, 401
    session.clear()
    session.update(user_id=user["id"], role="operator", username=user["username"], name=user["display_name"])
    return {"user": {"id": user["id"], "username": user["username"], "name": user["display_name"]}, "csrf_token": csrf_token()}


@auth_bp.post("/logout")
def logout():
    if not valid_csrf():
        return {"error": "요청 확인 값이 만료되었습니다. 새로고침 후 다시 시도해 주세요."}, 403
    session.clear()
    return {"user": None}
