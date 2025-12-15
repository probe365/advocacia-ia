from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    current_app,
)
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from models import User
from cadastro_manager import CadastroManager
from flask import g

bp = Blueprint('auth', __name__)

# Lazy manager per request (respects tenant in g if set)

def _manager(global_admin: bool = False):
    return CadastroManager(getattr(g, 'tenant_id', None), is_global_admin=global_admin)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_data = _manager(global_admin=True).get_usuario_by_username(username)
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data)
            login_user(user)
            tenant = user_data.get('tenant_id') or current_app.config.get('DEFAULT_TENANT_ID')
            session['tenant_id'] = tenant
            g.tenant_id = tenant
            return redirect(url_for('clientes.ui_mostrar_clientes'))
        flash('Nome de usuário ou senha inválidos.', 'danger')
    return render_template('login.html')

@bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nome_completo = request.form.get('nome_completo')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password != confirm_password:
            flash('As senhas não coincidem.', 'danger')
            return redirect(url_for('auth.registro'))
        if _manager().get_usuario_by_username(username):
            flash('Usuário já existe.', 'danger')
            return redirect(url_for('auth.registro'))
        if _manager().create_usuario(username, email, password, nome_completo):
            flash('Conta criada. Faça login.', 'success')
            return redirect(url_for('auth.login'))
        flash('Erro ao criar conta.', 'danger')
    return render_template('registro.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('tenant_id', None)
    flash('Logout realizado.', 'success')
    return redirect(url_for('auth.login'))
