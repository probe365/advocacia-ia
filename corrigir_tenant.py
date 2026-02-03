from cadastro_manager import CadastroManager

# Exemplo de dados do cliente
dados_cliente = {
    "tipo_pessoa": "Física",
    "nome_completo": "Adolfo da Silva",
    "cpf_cnpj": "345.987.231-34",
    "telefone": "1198763459",
    "email": "asilva@gmail.com"
    # Adicione outros campos conforme necessário
}

# Instancie o CadastroManager com o tenant_id correto (ex: 'public')
manager = CadastroManager(tenant_id="public")

# Crie o cliente
novo_id = manager.save_cliente(dados_cliente)

print("ID do novo cliente:", novo_id)
