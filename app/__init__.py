# app/__init__.py
from flask import Flask, g
from pathlib import Path
import os

from config import get_config
from app.extensions import db, migrate, login_manager

from .health import health_bp
from .metrics import metrics_bp
from .blueprints.clientes import clientes_bp
from .blueprints.processos import processos_bp
from .blueprints.kb import kb_bp
from .blueprints.escritorio import escritorio_bp
from .blueprints.auth import bp as auth_bp
from .blueprints.documentos import bp as documentos_bp
from .middleware import before_request, after_request
from logging_config import init_logging
from models import User
from cadastro_manager import CadastroManager

# AI/ML blueprints (conditional)
MINIMAL_MODE = os.environ.get('MINIMAL_MODE') == '1'

if not MINIMAL_MODE:
    from .blueprints.ementas import ementas_bp
    from .blueprints.ementas_faiss import ementas_faiss
    from .blueprints.chat import bp as chat_bp
    from .blueprints.inference import bp as inference_bp
    from app.services.ementas_client import EmentasSearchClient


def create_app():
    # Resolve project root
    base_dir = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(base_dir / "templates"),
        static_folder=str(base_dir / "static")
    )

    cfg = get_config()()
    app.config.from_object(cfg)
    app.secret_key = cfg.SECRET_KEY

    init_logging(cfg.LOG_LEVEL)

    # --- INIT EXTENSIONS ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # --- INIT Ementas Client ---
    if not MINIMAL_MODE:
        try:
            ementas_client = EmentasSearchClient(
                model_name=cfg.EMENTAS_EMB_MODEL,
                index_path=Path(cfg.EMENTAS_INDEX_PATH),
                store_path=Path(cfg.EMENTAS_STORE_PATH),
                normalize=True
            )
            app.extensions["ementas"] = ementas_client
        except Exception as e:
            app.logger.error(f"Falha ao iniciar EmentasSearchClient: {e}")
            app.extensions["ementas"] = None

    # --- BLUEPRINTS ---
    app.register_blueprint(health_bp)

    if cfg.METRICS_ENABLED:
        app.register_blueprint(metrics_bp)

    app.register_blueprint(auth_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(processos_bp)
    app.register_blueprint(kb_bp)
    app.register_blueprint(escritorio_bp)
    app.register_blueprint(documentos_bp)

    if not MINIMAL_MODE:
        app.register_blueprint(ementas_bp)
        app.register_blueprint(ementas_faiss)
        app.register_blueprint(chat_bp)
        app.register_blueprint(inference_bp)

    # --- MIDDLEWARE ---
    app.before_request(before_request)
    app.after_request(after_request)

    # --- LOGIN USER LOADER ---
    @login_manager.user_loader
    def load_user(user_id):
        tenant_id = getattr(g, "tenant_id", None)
        if tenant_id is None:
            return None
        mgr = CadastroManager(tenant_id)
        data = mgr.get_usuario_by_id(user_id)
        return User(data) if data else None

    # --- ROOT ROUTES ---
    @app.route("/")
    def index():
        return {"status": "ok", "msg": "Advocacia IA SaaS ativo!"}

    @app.route("/health")
    def health():
        return {"status": "healthy"}

    return app
