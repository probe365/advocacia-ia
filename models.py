# models.py
from flask_login import UserMixin

class User(UserMixin):
    """
    Classe que representa um usuário para o Flask-Login.
    Herda de UserMixin para obter implementações padrão de
    propriedades como is_authenticated, is_active, etc.
    """
    def __init__(self, user_data: dict):
        self.id = user_data.get('id')
        self.username = user_data.get('username')
        self.nome_completo = user_data.get('nome_completo')
        self.password_hash = user_data.get('password_hash')
        self.advogado_oab = user_data.get('advogado_oab')

    # Flask-Login usa o 'id' (que é um número inteiro) para gerenciar a sessão.
    def get_id(self):
        return str(self.id)