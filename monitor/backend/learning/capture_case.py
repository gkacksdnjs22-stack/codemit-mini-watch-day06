"""python -m learning.capture_case 12: 실제 요청의 DB 원본만 JSON으로 출력."""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from http.cookiejar import CookieJar
from time import monotonic, sleep
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import HTTPCookieProcessor, Request, build_opener

from learning.support import read_live, start_observation


def capture(count):
    base = os.getenv("GENERAL_SERVICE_URL", "http://general-api:5000").rstrip("/")
    address = urlparse(base)
    if address.scheme != "http" or address.hostname not in {"general-api", "localhost", "127.0.0.1"} or address.path or address.query or address.fragment or address.username:
        raise ValueError("로컬 일반 서비스 주소만 사용할 수 있습니다.")
    username, password = os.getenv("TRAINING_USERNAME"), os.getenv("TRAINING_PASSWORD")
    if not username or not password:
        raise ValueError("기존 일반 회원의 TRAINING_USERNAME과 TRAINING_PASSWORD를 환경변수로 설정하세요.")
    client = build_opener(HTTPCookieProcessor(CookieJar()))
    with client.open(base + "/login", timeout=10) as response:
        match = re.search(r'name="csrf_token" value="([^"]+)"', response.read().decode())
    if not match:
        raise ValueError("일반 로그인 화면의 CSRF 값을 읽지 못했습니다.")
    req = Request(base + "/api/auth/login", json.dumps({"username": username, "password": password}).encode(),
                  {"Content-Type": "application/json", "X-CSRF-Token": match[1]})
    with client.open(req, timeout=10) as response:
        user = json.load(response)["user"]
        if user.get("role") == "operator":
            raise ValueError("운영자가 아닌 일반 게시판 회원 계정을 사용하세요.")
    # 로그인 요청은 사례의 조회 횟수나 근거에 포함하지 않는다.
    after_id = start_observation()
    for _ in range(count):
        with client.open(base + "/", timeout=10) as response:
            if response.status != 200 or response.url != base + "/":
                raise ValueError("목록 GET / 가 직접 200으로 응답하지 않았습니다.")
            response.read()
    try:
        client.open(base + "/training-missing", timeout=10)
    except HTTPError as error:
        if error.code != 404:
            raise
        error.read()
    else:
        raise ValueError("없는 경로가 404로 응답하지 않았습니다.")
    deadline = monotonic() + 5
    while True:
        reference = datetime.now(timezone.utc)
        rows = read_live(after_id, reference)
        if len(rows) >= count + 1:
            break
        if monotonic() >= deadline:
            raise ValueError("감시 DB에 기록이 모두 도착하지 않았습니다. 일반 전송 경고와 감시 로그를 확인하세요.")
        sleep(0.1)
    views = [r for r in rows if r["method"] == "GET" and r["path"] == "/" and r["status_code"] == 200 and r["event_type"] == "post_list"]
    missing = [r for r in rows if r["path"] == "/training-missing" and r["status_code"] == 404 and r["event_type"] == "request_error"]
    if len(rows) != count + 1 or len(views) != count or len(missing) != 1:
        raise ValueError("요청 수·분류가 예상과 다릅니다. 다른 일반 요청을 멈추고 새 관찰부터 다시 실행하세요.")
    return {"after_id": after_id, "reference_time": reference.isoformat(), "records": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("count", type=int, choices=range(1, 101), metavar="1~100")
    args = parser.parse_args()
    try:
        result = capture(args.count)
    except Exception as error:
        # stdout의 실패 JSON이 기존 observation.json을 덮어쓰지 않도록 실패한다.
        print(f"캡처 실패: {type(error).__name__}. {error}" if isinstance(error, ValueError)
              else f"캡처 실패: {type(error).__name__}. 서버 로그와 계정 설정을 확인하세요.", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
