import os
from flask import Flask, request, abort
from auth_helpers import current_user
from observability import configure_errors

from routes.posts import posts_bp
from request_logging import register_request_logging
from routes.legacy import legacy_bp
from routes.auth import auth_bp
from auth_helpers import configure_session, template_auth

configure_errors("mini-general")
app = Flask(__name__)
app.json.ensure_ascii = False
configure_session(app)
app.register_blueprint(auth_bp)
app.register_blueprint(posts_bp)
app.register_blueprint(legacy_bp)
register_request_logging(app)
app.context_processor(template_auth)


@app.get("/health")
def health():
    return {"service": "general", "status": "ok"}


@app.get("/api/sentry-test")
def sentry_test():
    if os.getenv("ENABLE_SENTRY_TEST", "false").lower() != "true":
        abort(404)
    if current_user() is None:
        return {"error": "로그인이 필요합니다."}, 401
    # 실습 오류를 제거해 같은 로그인/활성화 조건에서 정상 응답합니다.
    result = 1 / 1
    return {"result": result}


@app.after_request
def private_response(response):
    if request.endpoint != "static":
        response.headers["Cache-Control"] = "no-store"
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
