"""DB 밖의 분석 경계와 인증·관찰 인수 검증. 실시간 요청 검증은 별도로 실행한다."""
import os
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

os.environ["SECRET_KEY"] = "analysis-test-key-longer-than-32-characters"
os.environ["SENTRY_DSN"] = ""
from app import app
from event_rules import make_event
from learning.normalize import normalize_event
from learning.http_rules import select_views, find_following_errors
from learning.report import build_report

BASE = datetime(2026, 10, 14, tzinfo=timezone.utc)


def row(number, seconds=0, **changes):
    return {"id": number, "method": "GET", "path": "/", "status_code": 200,
            "event_type": "post_list", "occurred_at": (BASE + timedelta(seconds=seconds)).isoformat(), **changes}


class AnalysisTests(unittest.TestCase):
    def test_source_is_preserved_and_four_filters_are_required(self):
        originals = [row(1), row(2, method="POST"), row(3, path="/board"), row(4, status_code=404), row(5, event_type="http_request")]
        saved = deepcopy(originals)
        events = [normalize_event(item) for item in originals]
        self.assertEqual(originals, saved)
        self.assertEqual([item["id"] for item in select_views(events)], ["http-1"])
        self.assertNotIn("ip", events[0])
        self.assertNotIn("user", events[0])
        self.assertEqual(events[0]["source"], "http_live")

    def test_error_time_boundaries_and_unsorted_latest_view(self):
        originals = [row(1, 10), row(2, 0), row(3, 9, status_code=404), row(4, 10, status_code=404), row(5, 40, status_code=404), row(6, 40.001, status_code=404), row(7, 11, status_code=500)]
        events = [normalize_event(item) for item in originals]
        self.assertEqual([item["id"] for item in find_following_errors(events, select_views(events))], ["http-5"])
        self.assertEqual(find_following_errors(events, []), [])

    def test_threshold_boundary_and_evidence_consistency(self):
        originals = [row(i + 1, i) for i in range(10)] + [row(11, 10, path="/training-missing", status_code=404, event_type="request_error")]
        first = build_report(originals, 10)["cards"][0]
        second = build_report(originals, 20)["cards"][0]
        self.assertTrue(first["matched"])
        self.assertFalse(second["matched"])
        self.assertEqual(first["observed"], 10)
        self.assertEqual(len(first["records"]), 11)
        self.assertEqual(first["evidence"], [item["id"] for item in first["records"]])
        self.assertEqual(first["records"], second["records"])
        self.assertEqual(build_report([], 10)["cards"][0]["evidence"], [])

    def test_event_classification_and_invalid_payloads(self):
        self.assertEqual(make_event(row(1))["event_type"], "post_list")
        self.assertEqual(make_event(row(2, status_code=404))["event_type"], "request_error")
        for data in (None, [], {"method": [], "path": "/", "status_code": 200}, row(1, status_code=True)):
            self.assertIsNone(make_event(data))

    def test_login_csrf_and_observation_validation(self):
        client = app.test_client()
        self.assertEqual(client.get("/api/analysis?after_id=0").status_code, 401)
        with patch("auth_helpers.current_user", return_value={"id": 1}):
            self.assertEqual(client.post("/api/analysis/observations").status_code, 403)
            for query in ("", "after_id=-1", "after_id=abc", "after_id=0&threshold=0", "after_id=0&threshold=1.5", "after_id=0&reference_time=2026-01-01", "after_id=0&reference_time=2999-01-01T00:00:00Z"):
                self.assertEqual(client.get("/api/analysis?" + query).status_code, 400)
            with patch("routes.analysis.read_live", return_value=[row(1)]) as read:
                first = client.get("/api/analysis?after_id=0&threshold=10").json
                second = client.get("/api/analysis", query_string={"after_id": 0, "threshold": 20, "reference_time": first["reference_time"]}).json
                self.assertEqual(first["reference_time"], second["reference_time"])
                self.assertEqual(read.call_args.args[1].isoformat(), first["reference_time"])


if __name__ == "__main__":
    unittest.main()
