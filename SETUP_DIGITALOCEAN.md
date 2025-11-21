# 🔧 Setup Guide - DigitalOcean
## Infraestrutura Completa | Advocacia e IA

**Data de Criação:** 11/11/2025  
**Versão:** 1.0  
**Plataforma:** DigitalOcean  
**Sistema Operacional:** Ubuntu 22.04 LTS  
**Status:** 📝 GUIA COMPLETO

---

## 📋 ÍNDICE

1. [Especificações do Servidor](#especificações-do-servidor)
2. [Passo 1: Criar Droplet](#passo-1-criar-droplet)
3. [Passo 2: Configuração Inicial](#passo-2-configuração-inicial)
4. [Passo 3: Instalar PostgreSQL 15](#passo-3-instalar-postgresql-15)
5. [Passo 4: Instalar Redis 7](#passo-4-instalar-redis-7)
6. [Passo 5: Instalar Python 3.11](#passo-5-instalar-python-311)
7. [Passo 6: Setup Aplicação Flask](#passo-6-setup-aplicação-flask)
8. [Passo 7: Configurar Nginx](#passo-7-configurar-nginx)
9. [Passo 8: Configurar SSL (Let's Encrypt)](#passo-8-configurar-ssl-lets-encrypt)
10. [Passo 9: Configurar Celery Workers](#passo-9-configurar-celery-workers)
11. [Passo 10: Backup Automático](#passo-10-backup-automático)
12. [Passo 11: Monitoramento](#passo-11-monitoramento)
13. [Manutenção e Troubleshooting](#manutenção-e-troubleshooting)

---

## 🖥️ ESPECIFICAÇÕES DO SERVIDOR

### Configuração Recomendada:

**Para MVP (até 10 tenants, 1000 processos):**
- **Droplet:** Basic Plan
- **CPU:** 2 vCPUs
- **RAM:** 4 GB
- **Storage:** 80 GB SSD
- **Bandwidth:** 4 TB
- **Custo Estimado:** ~$24/mês

**Para Produção (até 50 tenants, 10000 processos):**
- **Droplet:** General Purpose
- **CPU:** 4 vCPUs
- **RAM:** 8 GB
- **Storage:** 160 GB SSD
- **Bandwidth:** 5 TB
- **Custo Estimado:** ~$48/mês

### Regiões Recomendadas:
- **São Paulo (BR)** - Melhor latência para Brasil
- **New York (US)** - Alternativa estável
- **Toronto (CA)** - Opção intermediária

---

## 🚀 PASSO 1: CRIAR DROPLET

### 1.1 Acessar DigitalOcean
```bash
# Login em: https://cloud.digitalocean.com/
```

### 1.2 Criar Novo Droplet
1. Clique em **"Create" → "Droplets"**
2. Selecione:
   - **Image:** Ubuntu 22.04 LTS x64
   - **Plan:** Basic (4GB RAM / 2 vCPUs)
   - **Datacenter:** São Paulo 1
   - **Authentication:** SSH Keys (RECOMENDADO) ou Password

### 1.3 Configurações Adicionais
- **Hostname:** `advocacia-ia-prod`
- **Tags:** `producao`, `flask`, `multi-tenant`
- **Backups:** ✅ Ativar (adicional $4.80/mês)
- **Monitoring:** ✅ Ativar (gratuito)

### 1.4 Criar SSH Key (se não tiver)
```powershell
# No seu Windows local (PowerShell):
ssh-keygen -t ed25519 -C "seu_email@example.com"

# Salvar em: C:\Users\SeuUsuario\.ssh\id_ed25519
# Copiar chave pública:
cat C:\Users\SeuUsuario\.ssh\id_ed25519.pub
```

Colar a chave pública no campo **"New SSH Key"** no DigitalOcean.

### 1.5 Finalizar Criação
- Clique em **"Create Droplet"**
- Aguardar ~60 segundos (provisionamento)
- Anotar **IP público** (ex: `165.227.123.45`)

---

# Defina seu token (substitua pelo token real que copiou)
$TOKEN = "YOUR_TOKEN_HERE"

# Execute o comando para criar o droplet (PowerShell)
$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer $TOKEN"
}

$body = @{
    name = "advocacia-ia-prod"
    size = "s-2vcpu-4gb"
    region = "nyc3"
    image = "ubuntu-22-04-x64"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://api.digitalocean.com/v2/droplets" -Method Post -Headers $headers -Body $body


Adv0c@cia2025!IA
Adv0c@cia2025!IA

## 🔐 PASSO 2: CONFIGURAÇÃO INICIAL

### 2.1 Conectar ao Servidor
```powershell
# No PowerShell local:
ssh root@165.227.123.45
```

### 2.2 Atualizar Sistema
```bash
# No servidor Ubuntu:
apt update && apt upgrade -y
apt install -y curl wget git vim htop
```

### 2.3 Configurar Timezone
```bash
timedatectl set-timezone America/Sao_Paulo
date  # Verificar
```

### 2.4 Criar Usuário Não-Root
```bash
adduser appuser
usermod -aG sudo appuser

# Copiar SSH key para novo usuário:
rsync --archive --chown=appuser:appuser ~/.ssh /home/appuser
```

### 2.5 Configurar Firewall
```bash
ufw allow OpenSSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw enable

# Verificar status:
ufw status verbose
```

### 2.6 Testar Novo Usuário
```powershell
# Em nova janela PowerShell local:
ssh appuser@165.227.123.45
```

---

## 🐘 PASSO 3: INSTALAR POSTGRESQL 15

### 3.1 Adicionar Repositório Oficial
```bash
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update
```

### 3.2 Instalar PostgreSQL 15
```bash
sudo apt install -y postgresql-15 postgresql-contrib-15
```

### 3.3 Verificar Instalação
```bash
sudo systemctl status postgresql
# Deve estar "active (running)"

# Versão:
psql --version
# Output: psql (PostgreSQL) 15.x
```

### 3.4 Configurar PostgreSQL
```bash
# Entrar como usuário postgres:
sudo -u postgres psql

# No prompt psql:
CREATE DATABASE advocacia_ia_prod;
CREATE USER app_user WITH PASSWORD 'SuaSenhaSegura123!';
GRANT ALL PRIVILEGES ON DATABASE advocacia_ia_prod TO app_user;

# Ativar extensões necessárias:
\c advocacia_ia_prod
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

# Sair:
\q
```

### 3.5 Configurar Acesso Remoto (OPCIONAL)
```bash
sudo nano /etc/postgresql/15/main/postgresql.conf

# Alterar linha:
listen_addresses = 'localhost'  # Manter localhost por segurança

# Permitir apenas de IPs específicos:
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Adicionar linha (substituir SEU_IP_LOCAL):
host    advocacia_ia_prod    app_user    SEU_IP_LOCAL/32    md5

# Reiniciar:
sudo systemctl restart postgresql
```

### 3.6 Backup Inicial
```bash
# Criar diretório de backups:
sudo mkdir -p /var/backups/postgresql
sudo chown postgres:postgres /var/backups/postgresql

# Backup manual:
sudo -u postgres pg_dump advocacia_ia_prod > /var/backups/postgresql/inicial_$(date +%Y%m%d).sql
```

---

## 🔴 PASSO 4: INSTALAR REDIS 7

### 4.1 Instalar Redis
```bash
sudo apt install -y redis-server
```

### 4.2 Configurar Redis
```bash
sudo nano /etc/redis/redis.conf

# Alterar/adicionar linhas:
supervised systemd
bind 127.0.0.1 ::1
maxmemory 512mb
maxmemory-policy allkeys-lru
requirepass SuaSenhaRedis456!
```

### 4.3 Reiniciar Redis
```bash
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

### 4.4 Testar Conexão
```bash
redis-cli

# No prompt redis:
127.0.0.1:6379> AUTH SuaSenhaRedis456!
127.0.0.1:6379> PING
# Output: PONG
127.0.0.1:6379> SET test "Hello Redis"
127.0.0.1:6379> GET test
# Output: "Hello Redis"
127.0.0.1:6379> EXIT
```

---

## 🐍 PASSO 5: INSTALAR PYTHON 3.11

### 5.1 Instalar Python 3.11
```bash
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

### 5.2 Instalar pip
```bash
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11
python3.11 -m pip install --upgrade pip
```

### 5.3 Verificar Instalação
```bash
python3.11 --version
# Output: Python 3.11.x

python3.11 -m pip --version
# Output: pip 24.x
```

---

## 🌐 PASSO 6: SETUP APLICAÇÃO FLASK

### 6.1 Criar Diretório da Aplicação
```bash
sudo mkdir -p /var/www/advocacia-ia
sudo chown appuser:appuser /var/www/advocacia-ia
cd /var/www/advocacia-ia
```

### 6.2 Clonar Repositório
```bash
git clone https://github.com/seu-usuario/advocacia-ia.git .

# Ou copiar via SFTP (WinSCP, FileZilla):
# Local: C:\adv-IA-2910\
# Remoto: /var/www/advocacia-ia/
```

### 6.3 Criar Virtual Environment
```bash
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências:
pip install -r requirements.txt

# Instalar servidor WSGI:
pip install gunicorn
```

### 6.4 Configurar Variáveis de Ambiente
```bash
nano .env

# Adicionar:
FLASK_ENV=production
SECRET_KEY=sua_chave_secreta_super_aleatoria_aqui_123456789
DATABASE_URL=postgresql://app_user:SuaSenhaSegura123!@localhost/advocacia_ia_prod
REDIS_URL=redis://:SuaSenhaRedis456!@localhost:6379/0
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CELERY_BROKER_URL=redis://:SuaSenhaRedis456!@localhost:6379/0
CELERY_RESULT_BACKEND=redis://:SuaSenhaRedis456!@localhost:6379/1
```

### 6.5 Executar Migrations
```bash
source venv/bin/activate
flask db upgrade
```

### 6.6 Testar Aplicação Localmente
```bash
gunicorn --bind 0.0.0.0:8000 wsgi:app

# Em outro terminal, testar:
curl http://localhost:8000
# Deve retornar HTML da aplicação
```

### 6.7 Criar Serviço Systemd para Flask
```bash
sudo nano /etc/systemd/system/advocacia-ia.service

# Conteúdo:
[Unit]
Description=Gunicorn instance to serve Advocacia e IA
After=network.target

[Service]
User=appuser
Group=www-data
WorkingDirectory=/var/www/advocacia-ia
Environment="PATH=/var/www/advocacia-ia/venv/bin"
EnvironmentFile=/var/www/advocacia-ia/.env
ExecStart=/var/www/advocacia-ia/venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/var/www/advocacia-ia/advocacia-ia.sock \
    --timeout 120 \
    --access-logfile /var/log/advocacia-ia/access.log \
    --error-logfile /var/log/advocacia-ia/error.log \
    wsgi:app

[Install]
WantedBy=multi-user.target
```

### 6.8 Criar Diretório de Logs
```bash
sudo mkdir -p /var/log/advocacia-ia
sudo chown appuser:www-data /var/log/advocacia-ia
```

### 6.9 Iniciar Serviço
```bash
sudo systemctl start advocacia-ia
sudo systemctl enable advocacia-ia
sudo systemctl status advocacia-ia
```

---

## 🌐 PASSO 7: CONFIGURAR NGINX

### 7.1 Instalar Nginx
```bash
sudo apt install -y nginx
```

### 7.2 Criar Configuração do Site
```bash
sudo nano /etc/nginx/sites-available/advocacia-ia

# Conteúdo:
server {
    listen 80;
    server_name app.advocacia-ia.com.br *.advocacia-ia.com.br;

    client_max_body_size 50M;

    # Logs
    access_log /var/log/nginx/advocacia-ia-access.log;
    error_log /var/log/nginx/advocacia-ia-error.log;

    # Arquivos estáticos
    location /static {
        alias /var/www/advocacia-ia/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /uploads {
        alias /var/www/advocacia-ia/uploads;
        expires 7d;
    }

    # Proxy para Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/advocacia-ia/advocacia-ia.sock;
        
        # Timeouts para processos longos (geração de petições)
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
        
        # Headers adicionais
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
    }
}
```

### 7.3 Ativar Site
```bash
sudo ln -s /etc/nginx/sites-available/advocacia-ia /etc/nginx/sites-enabled/
sudo nginx -t  # Testar configuração
sudo systemctl restart nginx
```

### 7.4 Configurar DNS (no Provedor de Domínio)
```
# Adicionar registros A:
A     app.advocacia-ia.com.br         165.227.123.45
A     *.advocacia-ia.com.br           165.227.123.45

# Ou CNAME (se tiver domínio principal):
CNAME app.advocacia-ia.com.br         seudominio.com.br
CNAME *.advocacia-ia.com.br           seudominio.com.br
```

### 7.5 Testar Acesso HTTP
```powershell
# No Windows local:
curl http://app.advocacia-ia.com.br
# Deve retornar HTML da aplicação
```

---

## 🔒 PASSO 8: CONFIGURAR SSL (LET'S ENCRYPT)

### 8.1 Instalar Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 8.2 Obter Certificado SSL
```bash
sudo certbot --nginx -d app.advocacia-ia.com.br -d *.advocacia-ia.com.br
```

**NOTA:** Wildcard SSL (*.advocacia-ia.com.br) requer validação DNS:
```bash
# Certbot pedirá para adicionar registro TXT no DNS:
_acme-challenge.advocacia-ia.com.br TXT "valor-fornecido-pelo-certbot"

# Após adicionar, aguardar propagação DNS (5-10 min):
nslookup -type=TXT _acme-challenge.advocacia-ia.com.br

# Continuar no Certbot (pressionar Enter)
```

### 8.3 Configuração Automática pelo Certbot
O Certbot vai modificar `/etc/nginx/sites-available/advocacia-ia` automaticamente:
```nginx
server {
    listen 443 ssl http2;
    server_name app.advocacia-ia.com.br *.advocacia-ia.com.br;

    ssl_certificate /etc/letsencrypt/live/app.advocacia-ia.com.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.advocacia-ia.com.br/privkey.pem;
    
    # ... resto da configuração
}

server {
    listen 80;
    server_name app.advocacia-ia.com.br *.advocacia-ia.com.br;
    return 301 https://$server_name$request_uri;
}
```

### 8.4 Renovação Automática
```bash
# Testar renovação:
sudo certbot renew --dry-run

# Certbot cria cronjob automaticamente:
sudo systemctl status certbot.timer
```

### 8.5 Testar HTTPS
```powershell
# No Windows local:
curl https://app.advocacia-ia.com.br
# Deve retornar HTML com certificado válido
```

---

## ⚙️ PASSO 9: CONFIGURAR CELERY WORKERS

### 9.1 Criar Arquivo de Configuração Celery
```bash
nano /var/www/advocacia-ia/celery_config.py

# Conteúdo:
from celery import Celery
import os

broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'America/Sao_Paulo'
enable_utc = True

# Configuração Beat (scheduler)
beat_schedule = {
    'robot-pje-diario': {
        'task': 'tasks.buscar_comunicacoes_pje_diario',
        'schedule': crontab(hour=6, minute=0),  # Todo dia às 6h
    },
}
```

### 9.2 Criar Serviço Systemd para Celery Worker
```bash
sudo nano /etc/systemd/system/celery-worker@.service

# Conteúdo:
[Unit]
Description=Celery Worker Instance %i
After=network.target redis-server.service postgresql.service

[Service]
Type=forking
User=appuser
Group=www-data
WorkingDirectory=/var/www/advocacia-ia
Environment="PATH=/var/www/advocacia-ia/venv/bin"
EnvironmentFile=/var/www/advocacia-ia/.env
ExecStart=/var/www/advocacia-ia/venv/bin/celery -A celery_app worker \
    --loglevel=info \
    --logfile=/var/log/celery/worker-%i.log \
    --pidfile=/var/run/celery/worker-%i.pid \
    --hostname=worker-%i@%%h

[Install]
WantedBy=multi-user.target
```

### 9.3 Criar Serviço Celery Beat (Scheduler)
```bash
sudo nano /etc/systemd/system/celery-beat.service

# Conteúdo:
[Unit]
Description=Celery Beat Scheduler
After=network.target redis-server.service

[Service]
Type=simple
User=appuser
Group=www-data
WorkingDirectory=/var/www/advocacia-ia
Environment="PATH=/var/www/advocacia-ia/venv/bin"
EnvironmentFile=/var/www/advocacia-ia/.env
ExecStart=/var/www/advocacia-ia/venv/bin/celery -A celery_app beat \
    --loglevel=info \
    --logfile=/var/log/celery/beat.log \
    --pidfile=/var/run/celery/beat.pid

[Install]
WantedBy=multi-user.target
```

### 9.4 Criar Diretórios Necessários
```bash
sudo mkdir -p /var/log/celery
sudo mkdir -p /var/run/celery
sudo chown appuser:www-data /var/log/celery
sudo chown appuser:www-data /var/run/celery
```

### 9.5 Iniciar 5 Workers Paralelos
```bash
# Iniciar workers (1 a 5):
sudo systemctl start celery-worker@1
sudo systemctl start celery-worker@2
sudo systemctl start celery-worker@3
sudo systemctl start celery-worker@4
sudo systemctl start celery-worker@5

# Iniciar Beat:
sudo systemctl start celery-beat

# Ativar na inicialização:
sudo systemctl enable celery-worker@{1..5}
sudo systemctl enable celery-beat
```

### 9.6 Verificar Status
```bash
sudo systemctl status celery-worker@1
sudo systemctl status celery-beat

# Ver logs:
tail -f /var/log/celery/worker-1.log
```

### 9.7 Instalar Flower (Monitor Celery)
```bash
source /var/www/advocacia-ia/venv/bin/activate
pip install flower

# Criar serviço:
sudo nano /etc/systemd/system/celery-flower.service

# Conteúdo:
[Unit]
Description=Celery Flower Monitoring
After=network.target redis-server.service

[Service]
Type=simple
User=appuser
Group=www-data
WorkingDirectory=/var/www/advocacia-ia
Environment="PATH=/var/www/advocacia-ia/venv/bin"
EnvironmentFile=/var/www/advocacia-ia/.env
ExecStart=/var/www/advocacia-ia/venv/bin/celery -A celery_app flower \
    --port=5555 \
    --basic_auth=admin:senha_flower_123

[Install]
WantedBy=multi-user.target

# Iniciar:
sudo systemctl start celery-flower
sudo systemctl enable celery-flower

# Acessar: http://SEU_IP:5555
```

---

## 💾 PASSO 10: BACKUP AUTOMÁTICO

### 10.1 Criar Script de Backup
```bash
sudo nano /usr/local/bin/backup-advocacia-ia.sh

# Conteúdo:
#!/bin/bash
# Backup automático - Advocacia e IA

# Configurações
BACKUP_DIR="/var/backups/advocacia-ia"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="advocacia_ia_prod"
DB_USER="app_user"
DB_PASS="SuaSenhaSegura123!"

# Criar diretório se não existir
mkdir -p "$BACKUP_DIR/postgres"
mkdir -p "$BACKUP_DIR/uploads"
mkdir -p "$BACKUP_DIR/kb_stores"

# Backup PostgreSQL
echo "[$(date)] Backup PostgreSQL iniciado..."
PGPASSWORD="$DB_PASS" pg_dump -U "$DB_USER" -h localhost "$DB_NAME" | gzip > "$BACKUP_DIR/postgres/backup_$DATE.sql.gz"

# Backup uploads e KB stores
echo "[$(date)] Backup arquivos iniciado..."
tar -czf "$BACKUP_DIR/uploads/uploads_$DATE.tar.gz" -C /var/www/advocacia-ia uploads/
tar -czf "$BACKUP_DIR/kb_stores/kb_stores_$DATE.tar.gz" -C /var/www/advocacia-ia kb_store/ kb_cliente_store/ kb_global/

# Remover backups antigos (manter últimos 7 dias)
find "$BACKUP_DIR" -type f -mtime +7 -delete

echo "[$(date)] Backup concluído!"
```

### 10.2 Dar Permissão de Execução
```bash
sudo chmod +x /usr/local/bin/backup-advocacia-ia.sh
```

### 10.3 Configurar Cron (Backup Diário 2AM)
```bash
sudo crontab -e

# Adicionar linha:
0 2 * * * /usr/local/bin/backup-advocacia-ia.sh >> /var/log/backup-advocacia-ia.log 2>&1
```

### 10.4 Testar Backup Manual
```bash
sudo /usr/local/bin/backup-advocacia-ia.sh

# Verificar:
ls -lh /var/backups/advocacia-ia/postgres/
ls -lh /var/backups/advocacia-ia/uploads/
```

### 10.5 Backup Remoto (DigitalOcean Spaces - OPCIONAL)
```bash
# Instalar s3cmd:
sudo apt install -y s3cmd

# Configurar:
s3cmd --configure
# Preencher com credenciais do DigitalOcean Spaces

# Adicionar ao script de backup:
echo "[$(date)] Upload para DigitalOcean Spaces..."
s3cmd sync "$BACKUP_DIR/" s3://advocacia-ia-backups/$(hostname)/
```

---

## 📊 PASSO 11: MONITORAMENTO

### 11.1 Instalar htop (Monitor de Recursos)
```bash
sudo apt install -y htop
htop  # Executar e verificar uso de CPU/RAM
```

### 11.2 Configurar Logrotate
```bash
sudo nano /etc/logrotate.d/advocacia-ia

# Conteúdo:
/var/log/advocacia-ia/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 appuser www-data
    sharedscripts
    postrotate
        systemctl reload advocacia-ia > /dev/null 2>&1 || true
    endscript
}

/var/log/celery/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 appuser www-data
}
```

### 11.3 Instalar Prometheus Node Exporter (OPCIONAL)
```bash
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
tar -xvf node_exporter-1.6.1.linux-amd64.tar.gz
sudo mv node_exporter-1.6.1.linux-amd64/node_exporter /usr/local/bin/

# Criar serviço:
sudo nano /etc/systemd/system/node_exporter.service

# Conteúdo:
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target

# Iniciar:
sudo systemctl start node_exporter
sudo systemctl enable node_exporter

# Acessar métricas: http://SEU_IP:9100/metrics
```

### 11.4 Uptime Robot (Monitoramento Externo)
1. Acessar: https://uptimerobot.com/
2. Criar conta gratuita
3. Adicionar monitor:
   - **Type:** HTTP(s)
   - **URL:** https://app.advocacia-ia.com.br/health
   - **Interval:** 5 minutos
4. Configurar alertas por email

### 11.5 Criar Endpoint de Health Check
```python
# Em app.py ou health.py:
@app.route('/health')
def health_check():
    # Verificar BD
    try:
        db.session.execute('SELECT 1')
        db_status = 'ok'
    except:
        db_status = 'error'
    
    # Verificar Redis
    try:
        redis_client.ping()
        redis_status = 'ok'
    except:
        redis_status = 'error'
    
    return jsonify({
        'status': 'ok' if db_status == 'ok' and redis_status == 'ok' else 'degraded',
        'database': db_status,
        'redis': redis_status,
        'timestamp': datetime.now().isoformat()
    })
```

---

## 🛠️ MANUTENÇÃO E TROUBLESHOOTING

### 12.1 Comandos Úteis

#### Verificar Status dos Serviços:
```bash
sudo systemctl status advocacia-ia
sudo systemctl status celery-worker@1
sudo systemctl status celery-beat
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis-server
```

#### Ver Logs em Tempo Real:
```bash
# Flask:
tail -f /var/log/advocacia-ia/error.log

# Celery:
tail -f /var/log/celery/worker-1.log

# Nginx:
tail -f /var/log/nginx/advocacia-ia-error.log
```

#### Reiniciar Serviços:
```bash
sudo systemctl restart advocacia-ia
sudo systemctl restart celery-worker@{1..5}
sudo systemctl restart celery-beat
sudo systemctl restart nginx
```

#### Verificar Uso de Disco:
```bash
df -h
du -sh /var/www/advocacia-ia/*
```

#### Verificar Conexões PostgreSQL:
```bash
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
```

#### Limpar Cache Redis:
```bash
redis-cli
> AUTH SuaSenhaRedis456!
> FLUSHDB  # Limpar database atual
> FLUSHALL  # Limpar TODOS os databases (cuidado!)
```

### 12.2 Problemas Comuns

#### Problema: "502 Bad Gateway"
**Causa:** Gunicorn não está rodando ou socket não existe.
```bash
# Verificar:
sudo systemctl status advocacia-ia
ls -l /var/www/advocacia-ia/advocacia-ia.sock

# Reiniciar:
sudo systemctl restart advocacia-ia
```

#### Problema: "Database connection error"
**Causa:** PostgreSQL não está rodando ou credenciais incorretas.
```bash
# Verificar:
sudo systemctl status postgresql
sudo -u postgres psql -c "\l"  # Listar databases

# Testar conexão:
psql -U app_user -h localhost -d advocacia_ia_prod
```

#### Problema: "Celery tasks not executing"
**Causa:** Workers parados ou Redis inacessível.
```bash
# Verificar workers:
sudo systemctl status celery-worker@1

# Verificar Redis:
redis-cli ping

# Ver fila de tasks:
redis-cli
> AUTH SuaSenhaRedis456!
> LLEN celery
```

#### Problema: "Out of memory"
**Causa:** Aplicação consumindo mais RAM que disponível.
```bash
# Verificar uso:
free -m
htop

# Reduzir workers Gunicorn:
sudo nano /etc/systemd/system/advocacia-ia.service
# Alterar: --workers 2 (em vez de 4)

# Ou aumentar RAM do Droplet (resize)
```

### 12.3 Atualização da Aplicação

```bash
cd /var/www/advocacia-ia

# Backup antes:
sudo /usr/local/bin/backup-advocacia-ia.sh

# Pull do repositório:
git pull origin main

# Ativar venv:
source venv/bin/activate

# Atualizar dependências:
pip install -r requirements.txt

# Executar migrations:
flask db upgrade

# Reiniciar serviços:
sudo systemctl restart advocacia-ia
sudo systemctl restart celery-worker@{1..5}

# Verificar logs:
tail -f /var/log/advocacia-ia/error.log
```

### 12.4 Restaurar Backup

```bash
# Parar aplicação:
sudo systemctl stop advocacia-ia
sudo systemctl stop celery-worker@{1..5}

# Restaurar PostgreSQL:
gunzip < /var/backups/advocacia-ia/postgres/backup_20251110_020000.sql.gz | \
    sudo -u postgres psql advocacia_ia_prod

# Restaurar arquivos:
cd /var/www/advocacia-ia
tar -xzf /var/backups/advocacia-ia/uploads/uploads_20251110_020000.tar.gz
tar -xzf /var/backups/advocacia-ia/kb_stores/kb_stores_20251110_020000.tar.gz

# Reiniciar:
sudo systemctl start advocacia-ia
sudo systemctl start celery-worker@{1..5}
```

---

## 📞 CHECKLIST FINAL

### ✅ Setup Inicial:
- [ ] Droplet criado (4GB RAM, Ubuntu 22.04)
- [ ] SSH key configurada
- [ ] Firewall ativado (portas 22, 80, 443)
- [ ] Timezone configurado (America/Sao_Paulo)

### ✅ Infraestrutura:
- [ ] PostgreSQL 15 instalado e configurado
- [ ] Redis 7 instalado e configurado
- [ ] Python 3.11 instalado
- [ ] Nginx instalado e configurado
- [ ] SSL (Let's Encrypt) ativo

### ✅ Aplicação:
- [ ] Código clonado em `/var/www/advocacia-ia`
- [ ] Virtual environment criado
- [ ] Dependências instaladas
- [ ] Migrations executadas
- [ ] Serviço systemd criado e ativo
- [ ] Gunicorn rodando (4 workers)

### ✅ Celery:
- [ ] 5 workers Celery ativos
- [ ] Celery Beat (scheduler) ativo
- [ ] Flower (monitor) instalado

### ✅ Backup & Monitoramento:
- [ ] Script de backup criado
- [ ] Cron diário configurado (2AM)
- [ ] Logrotate configurado
- [ ] Uptime Robot ativo
- [ ] Health check endpoint funcionando

### ✅ DNS & Domínio:
- [ ] Domínio apontando para IP do servidor
- [ ] Wildcard DNS configurado (*.advocacia-ia.com.br)
- [ ] HTTPS funcionando
- [ ] Certificado SSL renovação automática

---

## 🎯 PRÓXIMOS PASSOS

1. **Testar aplicação completa** em https://app.advocacia-ia.com.br
2. **Criar 3 tenants de demo** para apresentação
3. **Popular dados de exemplo** (processos, clientes)
4. **Executar testes de carga** (simular 10 usuários simultâneos)
5. **Monitorar logs** nas primeiras 24h

---

## 📚 REFERÊNCIAS

- **DigitalOcean Docs:** https://docs.digitalocean.com/
- **PostgreSQL Docs:** https://www.postgresql.org/docs/15/
- **Redis Docs:** https://redis.io/docs/
- **Nginx Docs:** https://nginx.org/en/docs/
- **Celery Docs:** https://docs.celeryq.dev/
- **Gunicorn Docs:** https://docs.gunicorn.org/

---

*Guia criado em 11/11/2025*  
*Última atualização: 11/11/2025*  
*Versão: 1.0*  
*Status: ✅ COMPLETO E TESTADO*
