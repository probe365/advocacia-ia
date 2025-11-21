# create_test_user.py
from cadastro_manager import CadastroManager
print("Criando usuário de teste...")
db_manager = CadastroManager()
#                      username, email,             password,    nome completo
sucesso = db_manager.create_usuario("admin", "admin@email.com", "admin123", "Administrador do Sistema")
if sucesso:
    print("Usuário 'admin' com senha 'admin123' criado com sucesso!")
else:
    print("Usuário 'admin' já existe ou ocorreu um erro.")