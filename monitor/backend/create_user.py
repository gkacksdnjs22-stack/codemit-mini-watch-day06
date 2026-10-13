"""각 앱의 .env가 가리키는 DB에 계정을 준비하며 기존 계정은 유지합니다."""
import os
from getpass import getpass
from db import connect_db
from werkzeug.security import generate_password_hash


def main():
    username = os.getenv("PRACTICE_USERNAME") or input("아이디: ").strip()
    password = os.getenv("PRACTICE_PASSWORD") or getpass("비밀번호 (10자 이상): ")
    if not username or len(password) < 10 or not password.strip():
        raise SystemExit("아이디와 10자 이상의 비밀번호를 입력해 주세요.")
    with connect_db() as conn:
        result = conn.execute(
            "INSERT INTO users (username, display_name, password_hash) VALUES (%s, %s, %s) ON CONFLICT (username) DO NOTHING",
            (username, os.getenv("PRACTICE_DISPLAY_NAME", "실습 운영자"), generate_password_hash(password)),
        )
    print("계정을 만들었습니다." if result.rowcount else "기존 계정을 유지합니다.")


if __name__ == "__main__":
    main()
