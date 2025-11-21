# Script de Inicializacao - DIA 1 (12/11/2025)
# Executar hoje 11h | Advocacia e IA

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host " ADVOCACIA E IA - DIA 1 (12/11)" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# 1. Ativar ambiente virtual
Write-Host "[1/10] Ativando ambiente virtual..." -ForegroundColor Yellow
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    .\venv\Scripts\Activate.ps1
    Write-Host "[OK] Ambiente virtual ativado" -ForegroundColor Green
} else {
    Write-Host "[AVISO] venv nao encontrado. Criando..." -ForegroundColor Yellow
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    Write-Host "[OK] venv criado e ativado" -ForegroundColor Green
}

Write-Host ""

# 2. Instalar/atualizar dependências
Write-Host "[2/10] Verificando dependencias..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "[OK] Dependencias atualizadas" -ForegroundColor Green

Write-Host ""

# 3. Verificar PostgreSQL
Write-Host "[3/10] Verificando PostgreSQL..." -ForegroundColor Yellow
# Adicionar PostgreSQL ao PATH temporariamente se necessario
$pgPaths = @(
    "C:\Program Files\PostgreSQL\17\bin",
    "C:\Program Files\PostgreSQL\16\bin",
    "C:\Program Files\PostgreSQL\15\bin",
    "C:\PostgreSQL\17\bin",
    "C:\PostgreSQL\16\bin"
)

foreach ($path in $pgPaths) {
    if (Test-Path $path) {
        $env:Path = "$path;$env:Path"
        Write-Host "[OK] PostgreSQL encontrado em: $path" -ForegroundColor Green
        break
    }
}

# Testar conexao
try {
    $pgVersion = psql --version 2>$null
    Write-Host "[OK] PostgreSQL: $pgVersion" -ForegroundColor Green
} catch {
    Write-Host "[AVISO] psql nao encontrado no PATH, mas continuando..." -ForegroundColor Yellow
}

Write-Host ""

# 4. Verificar Redis
Write-Host "[4/10] Verificando Redis..." -ForegroundColor Yellow
try {
    python -c "import redis; r = redis.Redis(); r.ping(); print('[OK] Redis conectado')"
    Write-Host "[OK] Redis funcionando" -ForegroundColor Green
} catch {
    Write-Host "[AVISO] Redis nao esta rodando ou nao conectou" -ForegroundColor Yellow
    Write-Host "   Inicie o Redis se necessario" -ForegroundColor Yellow
}

Write-Host ""

# 5. Verificar status atual das migrations
Write-Host "[5/10] Status atual das migrations:" -ForegroundColor Yellow
flask db current
Write-Host ""

# 6. Backup do banco ANTES das migrations
Write-Host "[6/10] Criando backup ANTES das migrations..." -ForegroundColor Yellow
$backupFile = "backup_12nov_ANTES_$(Get-Date -Format 'HHmm').sql"
try {
    $null = pg_dump -U postgres advocacia_ia_dev > $backupFile 2>$null
    if (Test-Path $backupFile) {
        Write-Host "[OK] Backup criado: $backupFile" -ForegroundColor Green
    } else {
        Write-Host "[AVISO] Backup nao foi criado (continuando...)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[AVISO] Erro ao criar backup (continuando...)" -ForegroundColor Yellow
}

Write-Host ""

# 7. Executar migrations 0005 e 0006
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host " EXECUTANDO MIGRATIONS" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[7/10] Migration 0005: Novos campos em processos..." -ForegroundColor Yellow
flask db upgrade
Write-Host ""

Write-Host "[8/10] Migration 0006: Tabela partes_adversas..." -ForegroundColor Yellow
flask db upgrade
Write-Host ""

# 8. Verificar estrutura final
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host " VERIFICANDO ESTRUTURA DO BD" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[9/10] Tabela processos:" -ForegroundColor Yellow
try {
    psql -U postgres -d advocacia_ia_dev -c "\d processos" 2>$null
} catch {
    Write-Host "[AVISO] Nao foi possivel verificar estrutura (use pgAdmin)" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "Tabela partes_adversas:" -ForegroundColor Yellow
try {
    psql -U postgres -d advocacia_ia_dev -c "\d partes_adversas" 2>$null
} catch {
    Write-Host "[AVISO] Nao foi possivel verificar estrutura (use pgAdmin)" -ForegroundColor Yellow
}
Write-Host ""

# 9. Backup DEPOIS das migrations
Write-Host "[10/10] Criando backup DEPOIS das migrations..." -ForegroundColor Yellow
$backupFileAfter = "backup_12nov_DEPOIS_$(Get-Date -Format 'HHmm').sql"
try {
    $null = pg_dump -U postgres advocacia_ia_dev > $backupFileAfter 2>$null
    if (Test-Path $backupFileAfter) {
        Write-Host "[OK] Backup pos-migration criado: $backupFileAfter" -ForegroundColor Green
    } else {
        Write-Host "[AVISO] Backup pos-migration nao foi criado" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[AVISO] Erro ao criar backup pos-migration" -ForegroundColor Yellow
}

Write-Host ""

# 10. Resumo final
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host " SETUP CONCLUIDO COM SUCESSO!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Proximos passos:" -ForegroundColor Yellow
Write-Host "1. Atualizar cadastro_manager.py (metodo save_processo)" -ForegroundColor White
Write-Host "2. Criar formulario templates/processo_edit.html" -ForegroundColor White
Write-Host "3. Implementar CRUD partes adversas" -ForegroundColor White
Write-Host "4. Testar tudo!" -ForegroundColor White
Write-Host ""
Write-Host "Ver: DIA_1_PLANO.md para detalhes" -ForegroundColor Cyan
Write-Host ""
Write-Host "Bom trabalho! Vamos fazer acontecer!" -ForegroundColor Green
Write-Host ""
