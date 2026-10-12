import os
from flask import Flask, request

from routes.posts import posts_bp
from request_logging import register_request_logging
from routes.legacy import legacy_bp
from routes.auth import auth_bp
from auth_helpers import configure_session, template_auth

app = Flask(__name__)
app.json.ensure_ascii = False
configure_session(app)
app.register_blueprint(auth_bp)
app.register_blueprint(posts_bp)
app.register_blueprint(legacy_bp)
register_request_logging(app)
app.context_processor(template_auth)


@app.after_request
def private_response(response):
    if request.endpoint != "static":
        response.headers["Cache-Control"] = "no-store"
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
