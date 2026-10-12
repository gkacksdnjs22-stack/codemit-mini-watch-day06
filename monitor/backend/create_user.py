"""실습용 계정을 준비합니다. 기존 계정은 유지합니다."""
import os
from db import connect_db
from werkzeug.security import generate_password_hash
with connect_db() as conn:
    result = conn.execute(
        "INSERT INTO users (username, display_name, password_hash) VALUES (%s, %s, %s) ON CONFLICT (username) DO NOTHING",
        (os.getenv("PRACTICE_USERNAME", "operator"), "실습 운영자", generate_password_hash(os.getenv("PRACTICE_PASSWORD", "Learn123!"))),
    )
print("계정을 만들었습니다." if result.rowcount else "기존 계정을 유지합니다.")
