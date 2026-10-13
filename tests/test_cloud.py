"""Run once per Flask folder to avoid their shared module names colliding."""
import os
import unittest
from unittest.mock import patch

os.environ["SECRET_KEY"] = "unit-test-key-with-more-than-32-characters"
os.environ["SENTRY_DSN"] = ""
os.environ["EVENT_TOKEN"] = "unit-event-token"
import app
import db
import auth_helpers
import observability


class CloudTests(unittest.TestCase):
    def test_health_needs_no_database(self):
        with patch.object(db, "connect_db", side_effect=AssertionError("DB called")):
            response = app.app.test_client().get("/health")
        self.assertEqual(response.status_code, 200)

    def test_sslmode_is_forwarded(self):
        env = {"DB_HOST":"pooler.example", "DB_PORT":"5432", "DB_NAME":"postgres",
               "DB_USER":"postgres.project", "DB_PASSWORD":"dummy", "DB_SSLMODE":"require"}
        with patch.dict(os.environ, env), patch("db.psycopg.connect") as connect:
            db.connect_db()
        self.assertEqual(connect.call_args.kwargs["sslmode"], "require")
        self.assertEqual(connect.call_args.kwargs["user"], "postgres.project")

    def test_secure_cookie_switch(self):
        with patch.dict(os.environ, {"SESSION_COOKIE_SECURE":"true"}):
            auth_helpers.configure_session(app.app)
        self.assertTrue(app.app.config["SESSION_COOKIE_SECURE"])
        with patch.dict(os.environ, {"SESSION_COOKIE_SECURE":"false"}):
            auth_helpers.configure_session(app.app)
        self.assertFalse(app.app.config["SESSION_COOKIE_SECURE"])

    def test_sentry_redacts_request_and_user(self):
        event = {"request":{"data":"password", "headers":{"Cookie":"secret"},
                            "cookies":"secret", "query_string":"token=secret", "method":"GET"},
                 "user":{"id":1}, "message":"example"}
        clean = observability.remove_request_secrets(event, {})
        self.assertEqual(clean["request"], {"method":"GET"})
        self.assertNotIn("user", clean)

    def test_sentry_environment_and_options(self):
        with patch.dict(os.environ, {"SENTRY_DSN":"https://public@example.test/1",
                                    "SENTRY_ENVIRONMENT":"unit", "APP_VERSION":"abc"}), \
             patch("observability.sentry_sdk.init") as init, \
             patch("observability.sentry_sdk.set_tag"):
            observability.configure_errors("test-service")
        self.assertEqual(init.call_args.kwargs["environment"], "unit")
        self.assertEqual(init.call_args.kwargs["release"], "abc")
        self.assertFalse(init.call_args.kwargs["send_default_pii"])
        self.assertFalse(init.call_args.kwargs["include_local_variables"])
        self.assertEqual(init.call_args.kwargs["max_request_body_size"], "never")

    def test_service_specific_routes(self):
        client = app.app.test_client()
        if hasattr(app, "sentry_test"):
            with patch("request_logging.requests.post"), patch("app.current_user",return_value=None):
                with patch.dict(os.environ, {"ENABLE_SENTRY_TEST":"false"}):
                    self.assertEqual(client.get("/api/sentry-test").status_code, 404)
                with patch.dict(os.environ, {"ENABLE_SENTRY_TEST":"true"}):
                    self.assertEqual(client.get("/api/sentry-test").status_code, 401)
                    with patch("app.current_user",return_value={"id":1}):
                        response = client.get("/api/sentry-test")
                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(response.json, {"result":1.0})
        else:
            with patch("routes.events.create_event") as save:
                for token in (None, "wrong"):
                    headers = {} if token is None else {"X-Event-Token":token}
                    self.assertEqual(client.post("/api/events",json={},headers=headers).status_code,403)
                response = client.post("/api/events",json={"method":"POST","path":"/login","status_code":401},
                                       headers={"X-Event-Token":"unit-event-token"})
                self.assertEqual(response.status_code,201)
                self.assertEqual(save.call_args.args[0]["event_type"],"login_failure")
                response = client.post("/api/events",json={"method":"POST","path":"/login","status_code":200},
                                       headers={"X-Event-Token":"unit-event-token"})
                self.assertEqual(save.call_args.args[0]["event_type"],"login_success")


if __name__ == "__main__":
    unittest.main()
