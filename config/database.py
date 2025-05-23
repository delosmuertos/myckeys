from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "storage" / "app.db"

SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_FILE}"
SQLALCHEMY_ECHO = False
