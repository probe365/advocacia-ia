from cadastro_manager import CadastroManager

if __name__ == "__main__":
    # Troque conforme seu tenant default (ex: public)
    mgr = CadastroManager(tenant_id="public")
    print(mgr.seed_process_participants())
