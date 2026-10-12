import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv(Path(__file__).with_name(".env"))


def connect_db():
    required = ("DB_NAME", "DB_USER", "DB_PASSWORD")
    if any(not os.getenv(name) for name in required):
        raise RuntimeError("general/.env에 DB 접속 정보를 입력해 주세요.")

    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        row_factory=dict_row,
        connect_timeout=5,
    )
