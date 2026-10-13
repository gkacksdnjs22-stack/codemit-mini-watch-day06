import hmac
import os
from flask import Blueprint, request
from repositories.events import create_event, list_events
from rules import make_event
from auth_helpers import api_access_error

events_bp = Blueprint("events", __name__, url_prefix="/api/events")


@events_bp.post("")
def receive_event():
    token = os.getenv("EVENT_TOKEN", "")
    if not token or not hmac.compare_digest(request.headers.get("X-Event-Token", ""), token):
        return {"error": "기록 전송 토큰이 올바르지 않습니다."}, 403
    event = make_event(request.get_json(silent=True))
    if event is None:
        return {"error": "method, path, status_code를 올바르게 보내 주세요."}, 400
    create_event(event)
    return {"message": "기록을 받았습니다."}, 201


@events_bp.get("")
def get_events():
    error = api_access_error()
    if error:
        return error
    event_type = request.args.get("event_type")
    if event_type is not None and event_type not in {"login_success", "login_failure", "http_request"}:
        return {"error": "지원하지 않는 이벤트 종류입니다."}, 400
    return {"events": list_events(event_type)}
