import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kasir.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

STRUK_DIR = os.getenv("STRUK_DIR", os.path.join(os.path.dirname(__file__), "static", "struk"))

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
CASHIER_PASSCODE = os.getenv("CASHIER_PASSCODE", "")
SECRET_KEY = os.getenv("SECRET_KEY", "dapoerasatoe-secret-key-change-in-prod-2026")

os.makedirs(STRUK_DIR, exist_ok=True)
