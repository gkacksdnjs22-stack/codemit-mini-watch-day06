from datetime import datetime, timezone
from flask import Blueprint, request
from auth_helpers import api_access_error
from learning.normalize import received_time
from learning.report import build_report
from learning.support import read_live, start_observation

analysis_bp = Blueprint("analysis", __name__, url_prefix="/api/analysis")


@analysis_bp.post("/observations")
def new_observation():
    error = api_access_error()
    if error:
        return error
    return {"after_id": start_observation(), "reference_time": None}


@analysis_bp.get("")
def analysis():
    error = api_access_error()
    if error:
        return error
    try:
        after_text = request.args.get("after_id", "")
        threshold_text = request.args.get("threshold", "10")
        if not after_text.isascii() or not after_text.isdecimal() or not threshold_text.isascii() or not threshold_text.isdecimal():
            raise ValueError("관찰 ID와 기준을 정수로 보내 주세요.")
        after_id, threshold = int(after_text), int(threshold_text)
        if after_id > 2147483647 or not 1 <= threshold <= 100000:
            raise ValueError("관찰 ID 또는 기준 범위가 올바르지 않습니다.")
        now = datetime.now(timezone.utc)
        reference = received_time(request.args["reference_time"]) if "reference_time" in request.args else now
        if reference > now:
            raise ValueError("기준시각은 미래일 수 없습니다.")
    except (ValueError, TypeError, OverflowError) as exc:
        return {"error": str(exc)}, 400
    report = build_report(read_live(after_id, reference), threshold)
    return {**report, "after_id": after_id, "reference_time": reference.isoformat(), "window_seconds": 60}
