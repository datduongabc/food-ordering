import os

# Must run before any `app` import: settings and the engine are created at import time.
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["SMTP_USERNAME"] = ""
os.environ["SMTP_PASSWORD"] = ""
for key in ("MOMO_PARTNER_CODE", "MOMO_ACCESS_KEY", "MOMO_SECRET_KEY"):
    os.environ[key] = ""  # live keys in a developer's shell must not reach the tests

# Integration and e2e tests use in-memory SQLite by default for speed. Point this at a
# throwaway Postgres server (e.g. postgresql+psycopg://postgres:postgres@127.0.0.1:55432/dateno_test)
# to run them against the production database engine; e2e creates and drops its own database.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite://")
