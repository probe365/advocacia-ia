from typing import Dict, List, Optional

from flask import g

from cadastro_manager import CadastroManager

class CadastroService:
    def __init__(self, manager: Optional[CadastroManager] = None):
        self._manager_override = manager

    def _get_manager(self) -> CadastroManager:
        if self._manager_override:
            return self._manager_override
        return CadastroManager(getattr(g, 'tenant_id', None))

    # Clientes
    def list_clientes(self) -> List[Dict]:
        return self._get_manager().get_clientes()

    def get_cliente(self, id_cliente: str) -> Optional[Dict]:
        return self._get_manager().get_cliente_by_id(id_cliente)

    def _merge_or_raise(self, fetch_fn, entity_id: str, dados: Dict, not_found_msg: str) -> Dict:
        atual = fetch_fn(entity_id)
        if not atual:
            raise ValueError(not_found_msg)
        return {**atual, **dados}

    def create_cliente(self, dados: Dict) -> Optional[str]:
        return self._get_manager().save_cliente(dados)

    
    
    def update_cliente(self, id_cliente: str, dados: Dict) -> Optional[str]:
        """
        Atualiza um cliente existente garantindo que:
        - o cliente pertença ao tenant atual (via manager)
        - campos não enviados sejam preservados
        """
        mgr = self._get_manager()
        merged = self._merge_or_raise(
            mgr.get_cliente_by_id,
            id_cliente,
            dados,
            f"Cliente {id_cliente} não encontrado para este tenant",
        )
        return mgr.save_cliente(merged, id_cliente=id_cliente)



    def delete_cliente(self, id_cliente: str) -> bool:
        return self._get_manager().delete_cliente(id_cliente)

    # Processos
    def list_processos_do_cliente(self, id_cliente: str) -> List[Dict]:
        return self._get_manager().get_processos_do_cliente(id_cliente)

    def create_processo(self, id_cliente: str, dados: Dict) -> Optional[str]:
        payload = {'id_cliente': id_cliente, **dados}
        return self._get_manager().save_processo(payload)

    def get_processo(self, id_processo: str) -> Optional[Dict]:
        return self._get_manager().get_processo_by_id(id_processo)

    def delete_processo(self, id_processo: str) -> bool:
        return self._get_manager().delete_processo(id_processo)

    def update_processo(self, id_processo: str, dados: Dict) -> Optional[str]:
        """Atualiza campos de um processo existente (inclui troca de advogado)."""
        merged = self._merge_or_raise(
            self.get_processo,
            id_processo,
            dados,
            "Processo não encontrado",
        )
        return self._get_manager().save_processo(merged, id_processo=id_processo)

    # Escritório (dados únicos)
    def get_escritorio(self) -> Dict:
        return self._get_manager().get_escritorio_info()

    def save_escritorio(self, dados: Dict) -> None:
        self._get_manager().save_escritorio(dados)

    # Advogados
    def list_advogados(self) -> List[Dict]:
        return self._get_manager().get_advogados()

    def save_advogado(self, dados: Dict, oab_original: Optional[str] = None):
        return self._get_manager().save_advogado(dados, oab_original=oab_original)

    def delete_advogado(self, oab: str):
        return self._get_manager().delete_advogado(oab)

    def get_advogado(self, oab: str) -> Optional[Dict]:
        return self._get_manager().get_advogado_by_oab(oab)
