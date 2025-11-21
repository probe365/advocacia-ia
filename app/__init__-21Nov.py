from flask import Flask, app
from pathlib import Path
import os

from flask_migrate import Migrate



# Check if running in minimal mode (for fast dev startup)
MINIMAL_MODE = os.environ.get('MINIMAL_MODE') == '1'

if not MINIMAL_MODE:
    from app.services.ementas_client import EmentasSearchClient
    
from config import get_config
from app.extensions import login_manager
from .health import health_bp
from .metrics import metrics_bp
from .blueprints.clientes import clientes_bp
from .blueprints.processos import processos_bp
from .blueprints.kb import kb_bp

if not MINIMAL_MODE:
    from .blueprints.ementas import ementas_bp
    from .blueprints.ementas_faiss import faiss_bp
    
from .blueprints.escritorio import escritorio_bp
from .blueprints.auth import bp as auth_bp
from .blueprints.documentos import bp as documentos_bp

if not MINIMAL_MODE:
    from .blueprints.chat import bp as chat_bp
    from .blueprints.inference import bp as inference_bp
    
from .middleware import before_request, after_request
from logging_config import init_logging
from models import User
from cadastro_manager import CadastroManager
from app.extensions import db  # Ensure db is imported for Migrate usage




def create_app():
    # Resolve project root two levels up from this file (app/ -> project root)
    base_dir = Path(__file__).resolve().parent.parent
    templates_dir = base_dir / 'templates'
    static_dir = base_dir / 'static'
    app = Flask(__name__, template_folder=str(templates_dir), static_folder=str(static_dir))
    cfg = get_config()()
    app.config.from_object(cfg)

    # Secret key (garanta que vem de variável de ambiente em produção)
    app.secret_key = cfg.SECRET_KEY

    # Logging (direcione para stdout/stderr em produção)
    init_logging(cfg.LOG_LEVEL)

    # Init extensions
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # 👉 NEW: inicializa o cliente de ementas uma vez (SKIP em modo minimal)
    if not MINIMAL_MODE:
        try:
            index_path = Path(cfg.EMENTAS_INDEX_PATH)
            store_path = Path(cfg.EMENTAS_STORE_PATH)
            model_name = cfg.EMENTAS_EMB_MODEL
            ementas_client = EmentasSearchClient(
                model_name=model_name,
                index_path=index_path,
                store_path=store_path,
                normalize=True
            )
            # expõe via extensions
            app.extensions["ementas"] = ementas_client
        except Exception as e:  # fail-safe em dev
            app.logger.exception("Falha ao iniciar EmentasSearchClient: %s", e)
            app.extensions["ementas"] = None  # evita crash do app
    else:
        app.logger.info("MINIMAL MODE: Ementas client disabled")
        app.extensions["ementas"] = None



    # Register blueprints
    app.register_blueprint(health_bp)
    if cfg.METRICS_ENABLED:
        app.register_blueprint(metrics_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(processos_bp)
    app.register_blueprint(kb_bp)
    
    # AI/ML blueprints (skip in minimal mode)
    if not MINIMAL_MODE:
        app.register_blueprint(ementas_bp)
        app.register_blueprint(faiss_bp)
    else:
        app.logger.info("MINIMAL MODE: Ementas/FAISS blueprints disabled")
        
    app.register_blueprint(escritorio_bp)
    app.register_blueprint(documentos_bp)
    
    # AI/ML dependent blueprints (skip in minimal mode)
    if not MINIMAL_MODE:
        app.register_blueprint(chat_bp)
        app.register_blueprint(inference_bp)
    else:
        app.logger.info("MINIMAL MODE: Chat/Inference blueprints disabled")

    app.before_request(before_request)
    app.after_request(after_request)

    # Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            from flask import g, current_app
            tenant_id = getattr(g, 'tenant_id', None)
            if tenant_id is None:
                current_app.logger.warning(f"[load_user] tenant_id is missing for user_id={user_id}. Possible misconfiguration in before_request or login flow.")
                # Optionally, raise an error for debugging:
                # raise RuntimeError("tenant_id is required in g for authenticated requests.")
                return None
            mgr = CadastroManager(tenant_id)
            data = mgr.get_usuario_by_id(user_id)
            if data:
                return User(data)
        except Exception as e:
            current_app.logger.error(f"[load_user] Exception: {e}")
            return None
        return None

    # SUGESTÃO: Adicione configuração para storage externo (S3/Blob) se for produção
    # app.config['STORAGE_BUCKET'] = os.environ.get('STORAGE_BUCKET', 'local')

    # SUGESTÃO: Adicione configuração para banco externo (RDS/CloudSQL)
    # app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

    # SUGESTÃO: Adicione healthcheck customizado para dependências externas

    # Rota principal para teste SaaS
    @app.route("/")
    def index():
        return {"status": "ok", "msg": "Advocacia IA SaaS ativo!"}

    # Healthcheck simples
    @app.route("/health")
    def health():
        return {"status": "healthy"}

    # ...depois de criar app e db:
    migrate = Migrate(app, db)

    return app