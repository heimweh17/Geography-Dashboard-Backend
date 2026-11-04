import os
from pathlib import Path


test_database = Path(__file__).with_name("health-test.db")
test_database.unlink(missing_ok=True)

os.environ["DATABASE_URL"] = f"sqlite:///{test_database.resolve().as_posix()}"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["ENVIRONMENT"] = "test"
