from cadastro_manager import CadastroManager

if __name__ == "__main__":
    mgr = CadastroManager()
    info = mgr.get_escritorio_info()
    print("Conexão OK, escritório:", info)
