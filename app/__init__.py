# app/__init__.py
from flask import Flask, app, g, session, redirect, url_for, got_request_exception
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(override=True)

from config import get_config
from app.extensions import db, migrate, login_manager
from flask_login import current_user

from .health import health_bp
from .metrics import metrics_bp
from .blueprints.clientes import clientes_bp
from .blueprints.processos import processos_bp
from .blueprints.kb import kb_bp
from .blueprints.escritorio import escritorio_bp
from .blueprints.auth import bp as auth_bp
from .blueprints.documentos import bp as documentos_bp
from .blueprints.dje import dje_bp
from .middleware import before_request, after_request
from logging_config import init_logging
from models import User
from cadastro_manager import CadastroManager
# from app.blueprints.dje_push_callback import bp_dje_push

from .blueprints.callback import callback_bp




from app.blueprints.petitions import petitions_bp


# AI/ML blueprints (conditional)
MINIMAL_MODE = os.environ.get('MINIMAL_MODE') == '1'

if not MINIMAL_MODE:
    from .blueprints.ementas import ementas_bp
    from .blueprints.ementas_faiss import ementas_faiss
    from .blueprints.chat import bp as chat_bp
    from .blueprints.inference import bp as inference_bp
    from app.services.ementas_client import EmentasSearchClient


def _init_ementas_client(app: Flask, cfg) -> None:
    if MINIMAL_MODE:
        return

    try:
        ementas_client = EmentasSearchClient(
            model_name=cfg.EMENTAS_EMB_MODEL,
            index_path=Path(cfg.EMENTAS_INDEX_PATH),
            store_path=Path(cfg.EMENTAS_STORE_PATH),
            normalize=True,
        )
        app.extensions["ementas"] = ementas_client
    except Exception as e:
        app.logger.error(f"Falha ao iniciar EmentasSearchClient: {e}")
        app.extensions["ementas"] = None


def _register_blueprints(app: Flask, cfg) -> None:
    app.register_blueprint(health_bp)

    if cfg.METRICS_ENABLED:
        app.register_blueprint(metrics_bp)

    app.register_blueprint(auth_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(processos_bp)
    app.register_blueprint(kb_bp)
    app.register_blueprint(escritorio_bp)
    app.register_blueprint(documentos_bp)
    app.register_blueprint(petitions_bp)

    # DJE painel
    app.register_blueprint(dje_bp)

    # DJE callback (FALTAVA ISSO)
    # app.register_blueprint(bp_dje_push)
    app.register_blueprint(callback_bp)

    if not MINIMAL_MODE:
        app.register_blueprint(ementas_bp)
        app.register_blueprint(ementas_faiss)
        app.register_blueprint(chat_bp)
        app.register_blueprint(inference_bp)



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
    _init_ementas_client(app, cfg)

    # --- BLUEPRINTS ---
    _register_blueprints(app, cfg)

    # --- MIDDLEWARE ---
    app.before_request(before_request)
    app.after_request(after_request)

    # --- ERROR LOGGING (preserva handler padrão) ---
    def _log_unhandled_exception(sender, exception, **extra):
        sender.logger.error("Unhandled exception", exc_info=exception)

    got_request_exception.connect(_log_unhandled_exception, app)

    @app.errorhandler(Exception)
    def _handle_exception(exc):
        app.logger.error("Unhandled exception (handler)", exc_info=exc)
        return "Internal Server Error", 500

    # --- LOGIN USER LOADER ---
    @login_manager.user_loader
    def load_user(user_id):
        tenant_id = session.get("tenant_id") or getattr(g, "tenant_id", None)
        if tenant_id is None:
            return None

        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            return None

        mgr = CadastroManager(tenant_id)
        data = mgr.get_usuario_by_id(user_id_int)
        return User(data) if data else None


    # --- ROOT ROUTES ---
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("clientes.ui_mostrar_clientes"))
        return redirect(url_for("auth.login"))

    @app.route("/health")
    def health():
        return {"status": "healthy"}

    return app
