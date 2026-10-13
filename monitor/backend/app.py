"""Flask 앱 생성과 라우터 등록. SQL은 repositories에서 실행합니다."""
import os
from observability import configure_errors
import psycopg
from flask import Flask
from routes.auth import auth_bp
from routes.events import events_bp
from routes.notes import notes_bp
from auth_helpers import configure_session


def create_app():
    configure_errors("mini-monitor")
    app = Flask(__name__)
    app.json.ensure_ascii = False
    configure_session(app)
    app.config["MAX_CONTENT_LENGTH"] = 1_000_000
    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(notes_bp)

    @app.after_request
    def no_cache(response):
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/health")
    def health():
        return {"service": "monitor", "status": "ok"}

    @app.errorhandler(psycopg.Error)
    def database_error(error):
        app.logger.error("DB 요청 실패: %s", type(error).__name__)
        return {"error": "DB에 연결하거나 자료를 처리할 수 없습니다. 잠시 후 다시 시도해 주세요."}, 503

    @app.errorhandler(413)
    def too_large(error):
        return {"error": "요청 내용이 너무 큽니다."}, 413

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
