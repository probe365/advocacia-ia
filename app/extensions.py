# app/extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

# Instâncias globais — IMPORTANTE!
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()

# Se futuramente você quiser registrar outras extensões (cache, celery, etc.),
# este é o arquivo certo para colocar.
