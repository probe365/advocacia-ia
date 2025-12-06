# 🐳 Docker - Estratégia de Implementação
## Advocacia e IA | Item 11 (Opcional)

**Data:** 11/11/2025  
**Implementação:** 06/12/2025 (Semana 4)  
**Status:** 📋 PLANEJADO  
**Prioridade:** 🟡 MÉDIA (não bloqueia MVP)

---

## 📊 DECISÃO ESTRATÉGICA

### ❌ NÃO Usar Docker AGORA (MVP até 28/11)

**Motivos:**
1. **Prazo Apertado:** 17 dias para MVP - cada hora conta
2. **Ambiente Funciona:** PostgreSQL + Redis já instalados localmente
3. **Time Familiarizado:** Todos sabem rodar Python venv
4. **Menos Complexidade:** Debug mais rápido sem containers
5. **Windows:** Possíveis problemas com Docker Desktop

**Ganho:** 4-6 horas economizadas na Semana 1

---

### ✅ Usar Docker DEPOIS (Fase 2 - 06/12)

**Motivos:**
1. **Deploy Produção:** DigitalOcean com containers é muito mais fácil
2. **Consistência:** Dev = Staging = Prod (mesma imagem)
3. **Escalabilidade:** 5 workers Celery = 5 containers
4. **CI/CD:** GitHub Actions → Build → Deploy automático
5. **Rollback Rápido:** Voltar para imagem anterior em segundos

**Ganho:** Infraestrutura profissional e escalável

---

## 🗓️ CRONOGRAMA

### **FASE 1 - MVP (12/11 - 28/11): SEM DOCKER**

**Desenvolvimento Local:**
```powershell
# Setup normal
cd C:\adv-IA-2910
.\venv\Scripts\activate
pip install -r requirements.txt
flask run

# PostgreSQL nativo Windows
# Redis nativo Windows
# Celery local
```

**Deploy DigitalOcean:** Manual (seguir `SETUP_DIGITALOCEAN.md`)

---

### **FASE 2 - Semana 4 (06/12): COM DOCKER**

**Sexta-feira 06/12 - DIA 20 (4 horas):**
- Dev #2 + #3: Dockerizar aplicação
- Paulo + Dev #1: Analisar PDFs petições

**Entregas:**
1. `Dockerfile` otimizado
2. `docker-compose.yml` completo (7 serviços)
3. `.dockerignore`
4. `nginx.conf`
5. Teste local funcionando
6. Documentação deployment

---

## 📋 ARQUITETURA DOCKER

### **Serviços (7 containers):**

```yaml
services:
  1. db          → PostgreSQL 15
  2. redis       → Redis 7
  3. app         → Flask + Gunicorn
  4. celery_worker → Celery (5 réplicas)
  5. celery_beat → Scheduler
  6. nginx       → Proxy reverso + SSL
  7. flower      → Monitor Celery (opcional)
```

### **Volumes:**
- `postgres_data` → Persistência BD
- `./uploads` → Arquivos enviados
- `./kb_store` → Vector stores RAG
- `./static` → CSS/JS
- `./certbot` → Certificados SSL

---

## 🔧 IMPLEMENTAÇÃO (06/12)

### **1. Dockerfile (30 minutos)**

```dockerfile
# Multi-stage build para otimizar tamanho
FROM python:3.11-slim as builder

WORKDIR /app

# Instalar dependências de sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage final
FROM python:3.11-slim

WORKDIR /app

# Copiar dependências do builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copiar aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p uploads kb_store kb_cliente_store kb_global logs

# Expor porta
EXPOSE 8000

# Comando padrão
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "wsgi:app"]
```

---

### **2. docker-compose.yml (1 hora)**

```yaml
version: '3.8'

services:
  # PostgreSQL
  db:
    image: postgres:15-alpine
    container_name: advocacia_db
    restart: always
    environment:
      POSTGRES_DB: advocacia_ia_prod
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    container_name: advocacia_redis
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 512mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Flask App
  app:
    build: .
    container_name: advocacia_app
    restart: always
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      FLASK_ENV: production
      DATABASE_URL: postgresql://app_user:${DB_PASSWORD}@db:5432/advocacia_ia_prod
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      CELERY_BROKER_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      CELERY_RESULT_BACKEND: redis://:${REDIS_PASSWORD}@redis:6379/1
      SECRET_KEY: ${SECRET_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    volumes:
      - ./uploads:/app/uploads
      - ./kb_store:/app/kb_store
      - ./kb_cliente_store:/app/kb_cliente_store
      - ./kb_global:/app/kb_global
      - ./logs:/app/logs
    ports:
      - "8000:8000"

  # Celery Workers (5 réplicas)
  celery_worker:
    build: .
    restart: always
    command: celery -A celery_app worker --loglevel=info --concurrency=2
    depends_on:
      - db
      - redis
      - app
    environment:
      DATABASE_URL: postgresql://app_user:${DB_PASSWORD}@db:5432/advocacia_ia_prod
      CELERY_BROKER_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      CELERY_RESULT_BACKEND: redis://:${REDIS_PASSWORD}@redis:6379/1
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    deploy:
      replicas: 5

  # Celery Beat (Scheduler)
  celery_beat:
    build: .
    container_name: advocacia_celery_beat
    restart: always
    command: celery -A celery_app beat --loglevel=info
    depends_on:
      - db
      - redis
    environment:
      DATABASE_URL: postgresql://app_user:${DB_PASSWORD}@db:5432/advocacia_ia_prod
      CELERY_BROKER_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      CELERY_RESULT_BACKEND: redis://:${REDIS_PASSWORD}@redis:6379/1

  # Nginx (Proxy Reverso)
  nginx:
    image: nginx:alpine
    container_name: advocacia_nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./static:/app/static:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    depends_on:
      - app

  # Flower (Monitor Celery - Opcional)
  flower:
    build: .
    container_name: advocacia_flower
    restart: always
    command: celery -A celery_app flower --port=5555 --basic_auth=admin:${FLOWER_PASSWORD}
    depends_on:
      - redis
    environment:
      CELERY_BROKER_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    ports:
      - "5555:5555"

volumes:
  postgres_data:

networks:
  default:
    name: advocacia_network
```

---

### **3. nginx.conf (30 minutos)**

```nginx
upstream app_server {
    server app:8000;
}

server {
    listen 80;
    server_name app.advocacia-ia.com.br *.advocacia-ia.com.br;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect HTTP to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name app.advocacia-ia.com.br *.advocacia-ia.com.br;

    # SSL
    ssl_certificate /etc/letsencrypt/live/app.advocacia-ia.com.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.advocacia-ia.com.br/privkey.pem;

    # SSL config
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

    client_max_body_size 50M;

    # Static files
    location /static {
        alias /app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to Flask
    location / {
        proxy_pass http://app_server;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

---

### **4. .dockerignore (5 minutos)**

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/
env/

# Git
.git/
.gitignore

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log
logs/

# Env
.env
.env.local

# Tests
.pytest_cache/
htmlcov/
.coverage

# OS
.DS_Store
Thumbs.db

# Uploads e KB (irão via volumes)
uploads/
kb_store/
kb_cliente_store/
kb_global/

# Backups
*.sql
backup_*
```

---

### **5. .env.example (15 minutos)**

```env
# Database
DB_PASSWORD=sua_senha_super_segura_aqui

# Redis
REDIS_PASSWORD=sua_senha_redis_aqui

# Flask
SECRET_KEY=sua_chave_secreta_aleatoria_aqui
FLASK_ENV=production

# OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx

# Celery
CELERY_BROKER_URL=redis://:sua_senha_redis_aqui@redis:6379/0
CELERY_RESULT_BACKEND=redis://:sua_senha_redis_aqui@redis:6379/1

# Flower (Monitor Celery)
FLOWER_PASSWORD=senha_flower_admin

# Domain
DOMAIN=app.advocacia-ia.com.br
```

---

## 🚀 COMANDOS ÚTEIS

### **Desenvolvimento Local:**
```powershell
# Build
docker-compose build

# Subir todos serviços
docker-compose up -d

# Ver logs
docker-compose logs -f app
docker-compose logs -f celery_worker

# Executar migrations
docker-compose exec app flask db upgrade

# Acessar shell do container
docker-compose exec app bash

# Parar tudo
docker-compose down

# Parar e remover volumes (CUIDADO!)
docker-compose down -v
```

### **Produção (DigitalOcean):**
```bash
# Deploy inicial
docker-compose -f docker-compose.prod.yml up -d

# Atualizar aplicação (zero downtime)
git pull
docker-compose build app
docker-compose up -d --no-deps --build app

# Backup
docker-compose exec db pg_dump -U app_user advocacia_ia_prod > backup.sql

# Monitorar
docker-compose ps
docker stats
```

---

## 📊 VANTAGENS x DESVANTAGENS

### ✅ Vantagens Docker:

1. **Isolamento:** Cada serviço em seu container
2. **Portabilidade:** Roda igual em dev/staging/prod
3. **Escalabilidade:** Aumentar workers = aumentar réplicas
4. **Versionamento:** Imagens com tags (v1.0, v1.1, etc)
5. **Rollback:** Voltar para imagem anterior instantaneamente
6. **CI/CD:** Integração fácil com GitHub Actions
7. **Orquestração:** Docker Compose gerencia tudo
8. **Logs Centralizados:** `docker-compose logs`

### ❌ Desvantagens Docker:

1. **Curva Aprendizado:** Time precisa conhecer Docker
2. **Overhead:** Containers usam mais RAM que processos nativos
3. **Complexidade Inicial:** Setup mais trabalhoso
4. **Debug:** Mais difícil debugar dentro de containers
5. **Windows:** Docker Desktop pode ter problemas

---

## 🎯 RECOMENDAÇÃO FINAL

### **Para MVP (até 28/11):**
❌ **NÃO usar Docker**
- Foco em funcionalidades
- Deploy manual mais rápido
- Time já conhece setup nativo

### **Para Fase 2 (dezembro):**
✅ **Dockerizar aplicação**
- Dia 06/12: Dockerização completa (4h)
- Testar local: `docker-compose up`
- Migrar DigitalOcean para Docker
- CI/CD GitHub Actions

### **Benefício:**
- MVP em 17 dias (sem perder tempo com Docker)
- Produção profissional com Docker depois
- Melhor dos dois mundos! 🚀

---

## 📚 REFERÊNCIAS

- **Docker Docs:** https://docs.docker.com/
- **Docker Compose:** https://docs.docker.com/compose/
- **PostgreSQL Container:** https://hub.docker.com/_/postgres
- **Redis Container:** https://hub.docker.com/_/redis
- **Nginx Container:** https://hub.docker.com/_/nginx
- **Best Practices:** https://docs.docker.com/develop/dev-best-practices/

---

*Documento criado: 11/11/2025*  
*Implementação: 06/12/2025*  
*Status: 📋 PLANEJADO*
