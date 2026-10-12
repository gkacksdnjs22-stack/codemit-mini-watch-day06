import os
from datetime import datetime, timezone
from time import perf_counter

import requests
from flask import g, request


def register_request_logging(app):
    app.config.setdefault(
        "MONITOR_URL", os.getenv("MONITOR_URL", "http://127.0.0.1:5200/api/events")
    )

    @app.before_request
    def start_timer():
        g.request_started = perf_counter()

    @app.after_request
    def record_request(response):
        if request.endpoint == "static":
            return response

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "path": request.path,
            "status_code": 200 if request.endpoint == "auth.login" and request.method == "POST" and response.status_code == 303 else response.status_code,
            "duration_ms": round((perf_counter() - g.request_started) * 1000, 2),
        }
        app.logger.info("request: %s", record)
        try:
            result = requests.post(app.config["MONITOR_URL"], json=record, timeout=0.5)
            result.raise_for_status()
        except requests.RequestException:
            app.logger.warning("감시 서버에 요청 기록을 전달하지 못했습니다.")
        return response
