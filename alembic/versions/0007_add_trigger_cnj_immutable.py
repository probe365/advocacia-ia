"""Item 2 - Add trigger to make numero_cnj immutable

Revision ID: 0007_add_trigger_cnj_immutable
Revises: 0006_create_partes_adversas
Create Date: 2025-11-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0007_add_trigger_cnj_immutable'
down_revision = '0006_create_partes_adversas'
branch_labels = None
depends_on = None


def upgrade():
    """
    Item 2 - Trigger de Imutabilidade do numero_cnj
    
    Implementa trigger PostgreSQL que impede alteração do campo numero_cnj 
    após a criação do processo. Garante integridade e rastreabilidade.
    
    Funcionamento:
    - Permite INSERT com qualquer valor de numero_cnj
    - Bloqueia UPDATE que tente modificar numero_cnj
    - Mensagem de erro: "O número CNJ não pode ser alterado após a criação do processo"
    - Trigger executado BEFORE UPDATE
    
    Casos de uso:
    - Impede alterações acidentais via interface
    - Impede alterações via API/scripts
    - Mantém histórico consistente
    - Conformidade com normas CNJ
    """
    
    # Função que será chamada pelo trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_cnj_update()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Verifica se numero_cnj está sendo alterado
            IF OLD.numero_cnj IS DISTINCT FROM NEW.numero_cnj THEN
                RAISE EXCEPTION 'O número CNJ não pode ser alterado após a criação do processo. Valor atual: %, tentativa de alteração: %', 
                    OLD.numero_cnj, NEW.numero_cnj
                    USING HINT = 'Se o número CNJ está incorreto, delete e recrie o processo',
                          ERRCODE = '23514';  -- check_violation
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Trigger na tabela processos
    op.execute("""
        CREATE TRIGGER trigger_prevent_cnj_update
        BEFORE UPDATE ON processos
        FOR EACH ROW
        EXECUTE FUNCTION prevent_cnj_update();
    """)
    
    print("✅ Trigger de imutabilidade do numero_cnj criado com sucesso")
    print("   - Campo numero_cnj não pode mais ser alterado após INSERT")
    print("   - Apenas exclusão + recriação permitida se houver erro")


def downgrade():
    """
    Remove trigger e função de imutabilidade do numero_cnj.
    
    ATENÇÃO: Isso permitirá novamente alterações no numero_cnj.
    Use apenas em desenvolvimento/testes.
    """
    
    # Remove trigger
    op.execute("DROP TRIGGER IF EXISTS trigger_prevent_cnj_update ON processos;")
    
    # Remove função
    op.execute("DROP FUNCTION IF EXISTS prevent_cnj_update();")
    
    print("⚠️ Trigger de imutabilidade do numero_cnj removido")
    print("   - numero_cnj pode ser alterado novamente (NÃO RECOMENDADO)")
