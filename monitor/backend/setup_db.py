"""DB 테이블 준비 / 별도의 실습 계정 생성 (기존 계정은 덮어쓰지 않습니다)."""
import argparse
import sys
from getpass import getpass
from pathlib import Path
from werkzeug.security import generate_password_hash
from db import connect_db


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", help="새 실습 계정 아이디. 생략하면 테이블만 준비")
    parser.add_argument("--name", default="운영자", help="화면에 표시할 이름")
    parser.add_argument("--password-stdin", action="store_true", help="자동 검증용: 표준 입력에서 비밀번호와 확인 값을 두 줄로 읽기")
    args = parser.parse_args()
    with connect_db() as conn:
        conn.execute(Path(__file__).with_name("sql").joinpath("dashboard.sql").read_text(encoding="utf-8"))
    print("감시 DB 테이블을 준비했습니다. 기존 자료는 유지됩니다.")
    if args.username is None:
        return
    username, name = args.username.strip(), args.name.strip()
    if not username or not name:
        parser.error("아이디와 표시 이름은 공백만 입력할 수 없습니다.")
    if args.password_stdin:
        password = sys.stdin.readline().rstrip("\r\n")
        confirmation = sys.stdin.readline().rstrip("\r\n")
    else:
        password = getpass("실습 계정 비밀번호 (8자 이상): ")
        confirmation = getpass("비밀번호 확인: ")
    if len(password) < 8 or not password.strip() or password != confirmation:
        parser.error("비밀번호는 8자 이상이며 확인 값과 같아야 합니다.")
    with connect_db() as conn:
        result = conn.execute(
            "INSERT INTO users (username, display_name, password_hash) VALUES (%s, %s, %s) ON CONFLICT (username) DO NOTHING",
            (username, name, generate_password_hash(password)),
        )
    print("계정을 만들었습니다." if result.rowcount else "이미 있는 계정입니다. 기존 비밀번호를 유지합니다.")


if __name__ == "__main__":
    main()
