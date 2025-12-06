# start_flask.ps1 - Inicializador Flask com Progress Bar
# Advocacia e IA - DIA 1 (12/11/2025)

param(
    [switch]$Debug = $false
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  ADVOCACIA E IA - FLASK APP STARTER" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# [1/5] Verificar Python
Write-Host "[1/5] Verificando Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Python nao encontrado. Instale Python 3.11+" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] $pythonVersion" -ForegroundColor Green

# [2/5] Verificar venv
Write-Host "[2/5] Verificando ambiente virtual..." -ForegroundColor Yellow
if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "  [AVISO] venv nao encontrado. Criando..." -ForegroundColor Yellow
    python -m venv venv
}

# Ativar venv
& .\venv\Scripts\Activate.ps1
Write-Host "  [OK] venv ativado" -ForegroundColor Green

# [3/5] Verificar dependencias criticas
Write-Host "[3/5] Verificando dependencias..." -ForegroundColor Yellow
$requiredPackages = @(
    "Flask",
    "psycopg2",
    "langchain",
    "openai",
    "gensim"
)

$missingPackages = @()
foreach ($pkg in $requiredPackages) {
    $installed = pip show $pkg 2>$null
    if ($LASTEXITCODE -ne 0) {
        $missingPackages += $pkg
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host "  [AVISO] Instalando pacotes faltantes: $($missingPackages -join ', ')" -ForegroundColor Yellow
    pip install -r requirements.txt --quiet --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [ERRO] Falha ao instalar dependencias" -ForegroundColor Red
        exit 1
    }
}
Write-Host "  [OK] Todas dependencias instaladas" -ForegroundColor Green

# [4/5] Verificar PostgreSQL
Write-Host "[4/5] Verificando PostgreSQL..." -ForegroundColor Yellow
$pgHost = $env:DB_HOST
if (-not $pgHost) { $pgHost = "localhost" }
$pgPort = $env:DB_PORT
if (-not $pgPort) { $pgPort = "5432" }

$pgTest = Test-NetConnection -ComputerName $pgHost -Port $pgPort -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
if ($pgTest.TcpTestSucceeded) {
    Write-Host "  [OK] PostgreSQL acessivel em ${pgHost}:${pgPort}" -ForegroundColor Green
} else {
    Write-Host "  [AVISO] PostgreSQL nao acessivel. Verifique se esta rodando." -ForegroundColor Yellow
}

# [5/5] Iniciar Flask
Write-Host "[5/5] Iniciando Flask App..." -ForegroundColor Yellow
Write-Host "  [INFO] Carregando modelos AI (pode levar 30-60s)..." -ForegroundColor Cyan

if ($Debug) {
    $env:FLASK_DEBUG = "1"
    Write-Host "  [DEBUG] Modo debug ativado" -ForegroundColor Magenta
}

# Criar job em background para mostrar spinner
$spinnerJob = Start-Job -ScriptBlock {
    $spinner = @('|', '/', '-', '\')
    $i = 0
    while ($true) {
        Start-Sleep -Milliseconds 200
        Write-Host "`r  [CARREGANDO] $($spinner[$i % 4]) SentenceTransformers, Gensim, ChromaDB..." -NoNewline -ForegroundColor Cyan
        $i++
    }
}

# Iniciar Flask
try {
    # Redirecionar stderr para capturar logs de inicializacao
    $process = Start-Process -FilePath "python" -ArgumentList "app.py" -NoNewWindow -PassThru -RedirectStandardError "flask_startup.log"
    
    # Aguardar 15 segundos para carregamento
    for ($i = 1; $i -le 15; $i++) {
        Start-Sleep -Seconds 1
        if ($process.HasExited) {
            Stop-Job $spinnerJob -ErrorAction SilentlyContinue
            Remove-Job $spinnerJob -ErrorAction SilentlyContinue
            Write-Host "`r" -NoNewline
            Write-Host "  [ERRO] Flask falhou ao iniciar. Veja flask_startup.log" -ForegroundColor Red
            Get-Content "flask_startup.log" | Select-Object -Last 20
            exit 1
        }
    }
    
    Stop-Job $spinnerJob -ErrorAction SilentlyContinue
    Remove-Job $spinnerJob -ErrorAction SilentlyContinue
    Write-Host "`r                                                                                 " -NoNewline
    Write-Host "`r  [OK] Flask iniciado (PID: $($process.Id))" -ForegroundColor Green
    
    # Testar conectividade
    Start-Sleep -Seconds 2
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        Write-Host "`n[SUCESSO] App rodando em http://localhost:5000" -ForegroundColor Green
        Write-Host "          Status Code: $($response.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "`n[AVISO] Flask iniciado mas ainda carregando modelos..." -ForegroundColor Yellow
        Write-Host "        Tente acessar http://localhost:5000 em ~30 segundos" -ForegroundColor Yellow
    }
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  LOGS EM TEMPO REAL:" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "[CTRL+C para parar]`n" -ForegroundColor Gray
    
    # Aguardar processo (mostrar logs se debug)
    if ($Debug) {
        Get-Content "flask_startup.log" -Wait -Tail 50
    } else {
        $process.WaitForExit()
    }
    
} catch {
    Stop-Job $spinnerJob -ErrorAction SilentlyContinue
    Remove-Job $spinnerJob -ErrorAction SilentlyContinue
    Write-Host "`n[ERRO] Falha ao iniciar Flask: $_" -ForegroundColor Red
    exit 1
}
