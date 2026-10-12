"""두 gateway를 거쳐 로그인 기록/게시글/메모와 재시작 후 자료를 검증합니다.

실행: python verify_docker.py prepare 또는 python verify_docker.py persisted
prepare는 과제에서 요구하는 Docker 점검 메모를 남깁니다. persisted는 조회만 합니다.
"""
import argparse
import json
import re
from pathlib import Path
from urllib.request import HTTPCookieProcessor, Request, build_opener
from urllib.error import HTTPError
from http.cookiejar import CookieJar

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("phase", choices=["prepare", "persisted"])
args = parser.parse_args()
results = []

def check(name, condition):
    if not condition:
        raise AssertionError(name)
    results.append(name)
    print("PASS", name)

def client():
    return build_opener(HTTPCookieProcessor(CookieJar()))

def request(api, url, data=None, token=None):
    headers = {}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["X-CSRF-Token"] = token
    req = Request(url, json.dumps(data).encode() if data is not None else None, headers)
    try:
        response = api.open(req, timeout=10)
    except HTTPError as error:
        response = error
    raw = response.read().decode()
    try:
        raw = json.loads(raw)
    except ValueError:
        pass
    return response.status, raw

general, monitor = client(), client()
general_base, monitor_base = "http://localhost:8081", "http://localhost:8082"
status, session = request(monitor, monitor_base + "/api/auth/me")
check("감시 gateway/API 준비", status == 200 and "csrf_token" in session)
status, session = request(monitor, monitor_base + "/api/auth/login",
                          {"username": "operator", "password": "Learn123!"}, session["csrf_token"])
check("운영자 로그인", status == 200 and session["user"]["username"] == "operator")
token = session["csrf_token"]
for path in ["/", "/notes"]:
    status, page = request(monitor, monitor_base + path)
    check("Next.js production " + path, status == 200 and "Mini Watch" in page)

state_file = Path(__file__).with_name("verification-state.json")
if args.phase == "prepare":
    status, page = request(general, general_base + "/login")
    check("일반 로그인 화면", status == 200)
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', page)[1]
    status, body = request(general, general_base + "/api/auth/login",
                           {"username": "student", "password": "Wrong123!"}, csrf)
    check("로그인 실패 401", status == 401)
    status, body = request(general, general_base + "/api/auth/login",
                           {"username": "student", "password": "Learn123!"}, csrf)
    check("로그인 성공 200", status == 200 and body["user"]["username"] == "student")
    status, page = request(general, general_base + "/board")
    check("인증 후 게시판 접근", status == 200 and "모아" in page)
    status, events = request(monitor, monitor_base + "/api/events")
    failure = next(item for item in events["events"] if item["event_type"] == "login_failure" and item["status_code"] == 401)
    success = next(item for item in events["events"] if item["event_type"] == "login_success" and item["status_code"] == 200)
    check("실제 로그인 실패·성공 전달 및 DB 조회", status == 200)
    status, data = request(monitor, monitor_base + "/api/notes",
                           {"title": "Docker 점검", "body": "로그인 실패와 성공을 확인했다"}, token)
    check("메모 등록 201", status == 201)
    state = {"note_id": data["note"]["id"], "event_ids": [failure["id"], success["id"]]}
    state_file.write_text(json.dumps(state), encoding="utf-8")
else:
    state = json.loads(state_file.read_text(encoding="utf-8"))

# 새 쿠키 세션을 만들어 브라우저 새로고침/다시 로그인에 해당하는 재조회.
fresh = client()
_, initial = request(fresh, monitor_base + "/api/auth/me")
status, initial = request(fresh, monitor_base + "/api/auth/login",
                          {"username": "operator", "password": "Learn123!"}, initial["csrf_token"])
check("새 세션 운영자 로그인", status == 200)
status, notes = request(fresh, monitor_base + "/api/notes")
check("새 세션 메모 재조회", status == 200 and any(item["id"] == state["note_id"] and item["title"] == "Docker 점검" and item["body"] == "로그인 실패와 성공을 확인했다" for item in notes["notes"]))
status, events = request(fresh, monitor_base + "/api/events")
check("저장된 로그인 기록 유지", status == 200 and set(state["event_ids"]).issubset({item["id"] for item in events["events"]}))
Path(__file__).with_name(f"verification-{args.phase}.json").write_text(json.dumps({"phase": args.phase, "passed": results}, ensure_ascii=False, indent=2), encoding="utf-8")
