import os

SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "dev-only-secret-key-change-me")
SQLALCHEMY_DATABASE_URI = os.environ["SUPERSET_METADATA_URI"]

# local demo only: the setup script talks to the API without a CSRF token
WTF_CSRF_ENABLED = False
TALISMAN_ENABLED = False

FEATURE_FLAGS = {"DASHBOARD_NATIVE_FILTERS": True}
