import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
EMENTAS_FAISS_DIR = BASE_DIR / "data" / "ementas_faiss"


class BaseConfig:
    JSON_AS_ASCII = False
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", os.urandom(24))

    # Parâmetros "legacy" do CadastroManager (Postgres)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_NAME = os.getenv("DB_NAME", "advocacia_ia_prod")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "probe365")

    # Flask-SQLAlchemy (apenas para o `db` usado pelo Flask-Migrate)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///advocacia_ia.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flags de AI / comportamento
    ENABLE_AI = True
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    CASES_DIR = Path(os.getenv("CASES_DIR", "./cases"))
    MULTI_TENANT = os.getenv("MULTI_TENANT", "0") == "1"
    DEFAULT_TENANT_ID = os.getenv("DEFAULT_TENANT_ID", "public")
    METRICS_ENABLED = True
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # ---- Config de EMENTAS / FAISS ----
    EMENTAS_EMB_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    # pode ajustar esses paths depois, mas os atributos precisam existir:
    EMENTAS_INDEX_PATH = "data/ementas/faiss.index"
    EMENTAS_STORE_PATH = "data/ementas/store"


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "test": TestingConfig,
}


def get_config():
    env = os.getenv("FLASK_ENV", "development").lower()
    return config_map.get(env, DevelopmentConfig)
