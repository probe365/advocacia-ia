# app/services/petition_service.py
import sys
import os

# Garante que o Python encontre o cadastro_manager na raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from cadastro_manager import CadastroManager

class PetitionService:
    @staticmethod
    def preparar_contexto_peticao(id_processo, tenant_id):
        """
        Consolida dados do Postgres para preencher o formulário e a petição.
        Resolve a desconexão entre Processo e Partes Adversas.
        """
        mgr = CadastroManager(tenant_id=tenant_id)
        
        # 1. Busca dados básicos do processo
        proc = mgr.get_processo_by_id(id_processo)
        if not proc:
            return None

        # 2. Busca o Cliente (Autor)
        cliente = mgr.get_cliente_by_id(proc.get('id_cliente'))
        
        # 3. Busca o Advogado Responsável
        advogado = mgr.get_advogado_by_oab(proc.get('advogado_oab'))
        
        # 4. Busca Partes Adversas (Lógica central da Fase 2)
        partes = mgr.get_partes_adversas_by_processo(id_processo)
        # Consideramos a primeira parte como o réu principal para o formulário
        reu = partes[0] if partes else {}

        return {
            "processo": proc,
            "autor": cliente or {},
            "advogado": advogado or {},
            "reu": reu
        }