from typing import List, Dict, Optional
from cadastro_manager import CadastroManager

class CadastroService:
    def __init__(self, manager: Optional[CadastroManager] = None):
        self.manager = manager or CadastroManager()

    # Clientes
    def list_clientes(self) -> List[Dict]:
        return self.manager.get_clientes()

    def get_cliente(self, id_cliente: str) -> Optional[Dict]:
        return self.manager.get_cliente_by_id(id_cliente)

    def create_cliente(self, dados: Dict) -> str:
        return self.manager.save_cliente(dados)

    
    
    def update_cliente(self, id_cliente: str, dados: Dict) -> str:
        """
        Atualiza um cliente existente garantindo que:
        - o cliente pertença ao tenant atual (via manager)
        - campos não enviados sejam preservados
        """
        atual = self.manager.get_cliente_by_id(id_cliente)
        if not atual:
            raise ValueError(f"Cliente {id_cliente} não encontrado para este tenant")

        # Faz merge dos dados novos em cima do registro atual
        merged = {**atual, **dados}

        return self.manager.save_cliente(merged, id_cliente=id_cliente)



    def delete_cliente(self, id_cliente: str) -> bool:
        return self.manager.delete_cliente(id_cliente)

    # Processos
    def list_processos_do_cliente(self, id_cliente: str) -> List[Dict]:
        return self.manager.get_processos_do_cliente(id_cliente)

    def create_processo(self, id_cliente: str, dados: Dict) -> str:
        payload = {'id_cliente': id_cliente, **dados}
        return self.manager.save_processo(payload)

    def get_processo(self, id_processo: str) -> Optional[Dict]:
        return self.manager.get_processo_by_id(id_processo)

    def delete_processo(self, id_processo: str) -> bool:
        return self.manager.delete_processo(id_processo)

    def update_processo(self, id_processo: str, dados: Dict) -> str:
        """Atualiza campos de um processo existente (inclui troca de advogado)."""
        # Garantir que id do cliente permaneça
        atual = self.get_processo(id_processo)
        if not atual:
            raise ValueError("Processo não encontrado")
        merged = {**atual, **dados}
        return self.manager.save_processo(merged, id_processo=id_processo)

    # Escritório (dados únicos)
    def get_escritorio(self) -> Dict:
        return self.manager.get_escritorio_info()

    def save_escritorio(self, dados: Dict) -> None:
        self.manager.save_escritorio_info(dados)

    # Advogados
    def list_advogados(self) -> List[Dict]:
        return self.manager.get_advogados()

    def save_advogado(self, dados: Dict, oab_original: Optional[str] = None):
        return self.manager.save_advogado(dados, oab_original=oab_original)

    def delete_advogado(self, oab: str):
        return self.manager.delete_advogado(oab)

    def get_advogado(self, oab: str) -> Optional[Dict]:
        return self.manager.get_advogado_by_oab(oab)
