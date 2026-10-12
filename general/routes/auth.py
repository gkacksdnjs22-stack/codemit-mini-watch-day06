import os
import re
import json
from pathlib import Path

import psycopg
import requests
from flask import Blueprint, current_app, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from auth_helpers import current_user, valid_csrf
from repositories.users import create_user, find_user

auth_bp = Blueprint("auth", __name__)


def login_page(values, **context):
    manifest_path = Path(current_app.static_folder) / "portal/manifest.json"
    login_script = None
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        login_script = manifest["src/login-main.jsx"]["file"]
    return render_template("login.html", values=values, login_script=login_script, **context)


def login_error(values, message, status):
    if request.is_json or request.path == "/api/auth/login":
        return {"error": message}, status
    return login_page(values, error=message), status


def operator_username_exists(username):
    base = os.getenv("MONITOR_API_URL", "http://127.0.0.1:5200")
    response = requests.post(base + "/api/auth/account-exists", json={"username": username},
                             headers={"X-Internal-Auth": current_app.secret_key}, timeout=3)
    response.raise_for_status()
    return response.json()["exists"]


@auth_bp.get("/")
def home():
    user = current_user()
    if user:
        return redirect(os.getenv("DASHBOARD_URL", "http://127.0.0.1:5173/") if user["role"] == "operator" else url_for("posts.index"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
@auth_bp.post("/api/auth/login", endpoint="login_api")
def login():
    data = request.get_json(silent=True) if request.is_json else request.form
    if not isinstance(data, dict) and request.is_json:
        return {"error": "아이디와 비밀번호를 JSON 객체로 보내 주세요."}, 400
    username = data.get("username", "")
    password = data.get("password", "")
    if not isinstance(username, str) or not isinstance(password, str):
        return {"error": "아이디와 비밀번호를 문자열로 보내 주세요."}, 400
    values = {"username": username.strip()}
    if request.method == "GET":
        return login_page(values, registered=request.args.get("registered") == "1")
    if not valid_csrf():
        return login_error(values, "요청 확인 값이 만료되었습니다. 다시 시도해 주세요.", 403)
    if not values["username"] or not password.strip():
        return login_error(values, "아이디와 비밀번호를 모두 입력해 주세요.", 400)
    try:
        found = find_user(values["username"])
    except psycopg.Error:
        return login_error(values, "로그인 정보를 확인할 수 없습니다. 잠시 후 다시 시도해 주세요.", 503)
    # 계정이 등록된 저장소가 목적지를 결정합니다. 브라우저에서 역할을 고르거나 보내지 않습니다.
    if found is None:
        # 계정은 감시 DB에만 저장하며, 서버 간 API로 운영자 여부를 검증합니다.
        try:
            with requests.Session() as api:
                base = os.getenv("MONITOR_API_URL", "http://127.0.0.1:5200")
                initial = api.get(base + "/api/auth/me", timeout=3)
                initial.raise_for_status()
                response = api.post(base + "/api/auth/login", json={"username": values["username"], "password": password},
                                    headers={"X-CSRF-Token": initial.json()["csrf_token"]}, timeout=5)
                if response.status_code == 401:
                    return login_error(values, "아이디 또는 비밀번호가 올바르지 않습니다.", 401)
                response.raise_for_status()
                user = response.json()["user"]
                role = "operator"
        except (requests.RequestException, ValueError, KeyError):
            return login_error(values, "관리자 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.", 503)
    else:
        if not check_password_hash(found["password_hash"], password):
            return login_error(values, "아이디 또는 비밀번호가 올바르지 않습니다.", 401)
        user = {"id": found["id"], "username": found["username"], "name": found["display_name"]}
        role = "member"
    session.clear()
    session.update(user_id=user["id"], username=user["username"], name=user["name"], role=role)
    destination = os.getenv("DASHBOARD_URL", "http://127.0.0.1:5173/") if role == "operator" else url_for("posts.index")
    if request.is_json or request.path == "/api/auth/login":
        return {"user": {**user, "role": role}, "destination": destination}
    return redirect(destination, code=303)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    values = {key: request.form.get(key, "").strip() for key in ("username", "name")}
    if request.method == "GET":
        return render_template("signup.html", values=values)
    if not valid_csrf():
        return render_template("signup.html", values=values, error="요청 확인 값이 만료되었습니다. 다시 시도해 주세요."), 403
    password, confirmation = request.form.get("password", ""), request.form.get("confirmation", "")
    error = None
    if not re.fullmatch(r"[a-zA-Z0-9_]{3,32}", values["username"]):
        error = "아이디는 영문·숫자·밑줄로 3~32자 입력해 주세요."
    elif not 2 <= len(values["name"]) <= 50:
        error = "이름은 2~50자 입력해 주세요."
    elif not 10 <= len(password) <= 128 or not password.strip():
        error = "비밀번호는 10~128자 입력해 주세요."
    elif password != confirmation:
        error = "비밀번호 확인이 일치하지 않습니다."
    if error:
        return render_template("signup.html", values=values, error=error), 400
    try:
        if find_user(values["username"]) is not None or operator_username_exists(values["username"]):
            return render_template("signup.html", values=values, error="이미 사용 중인 아이디입니다."), 409
        create_user(values["username"], values["name"], generate_password_hash(password))
    except psycopg.errors.UniqueViolation:
        return render_template("signup.html", values=values, error="이미 사용 중인 아이디입니다."), 409
    except psycopg.Error:
        return render_template("signup.html", values=values, error="회원가입을 처리할 수 없습니다. 잠시 후 다시 시도해 주세요."), 503
    except (requests.RequestException, ValueError, KeyError):
        return render_template("signup.html", values=values, error="아이디 중복 확인을 할 수 없습니다. 잠시 후 다시 시도해 주세요."), 503
    return redirect(url_for("auth.login", registered="1"), code=303)


@auth_bp.post("/logout")
def logout():
    if not valid_csrf():
        return render_template("error.html", title="로그아웃 요청을 확인할 수 없습니다", message="화면을 새로고침하고 다시 시도해 주세요."), 403
    session.clear()
    return redirect(url_for("auth.login"), code=303)
