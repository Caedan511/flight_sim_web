import os
from pathlib import Path


from dotenv import load_dotenv



load_dotenv()


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Config:
    PROJECT_ROOT = PROJECT_ROOT
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "flight_sim_web")
    DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-development-secret")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 120))
    DATA_ROOT = Path(os.getenv("DATA_ROOT", str(PROJECT_ROOT / "data"))).resolve()
    SCRIPT_ALLOWED_EXTENSIONS = {
        ext.strip().lower()
        for ext in os.getenv("SCRIPT_ALLOWED_EXTENSIONS", ".json,.py,.m,.txt").split(",")
        if ext.strip()
    }
    SCRIPT_MAX_UPLOAD_BYTES = int(os.getenv("SCRIPT_MAX_UPLOAD_BYTES", 5 * 1024 * 1024))
    SIMULATION_WORKER_COUNT = int(os.getenv("SIMULATION_WORKER_COUNT", 3))
    SIMULATION_DEFAULT_MODEL_TYPE = os.getenv("SIMULATION_DEFAULT_MODEL_TYPE", "python_mock")
    SIMULATION_DEFAULT_MODEL_PATH = os.getenv("SIMULATION_DEFAULT_MODEL_PATH", "")
    SIMULATION_ALLOWED_MODEL_ROOTS = tuple(
        Path(path.strip()).resolve()
        for path in os.getenv("SIMULATION_ALLOWED_MODEL_ROOTS", str(PROJECT_ROOT / "models")).split(",")
        if path.strip()
    )
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]
