🧠 Advocacia e IA — Sistema Jurídico Inteligente

Plataforma moderna para escritórios de advocacia, combinando gestão de clientes, processos, documentos e análises jurídicas automatizadas com IA.
Desenvolvido com Flask + PostgreSQL e integrado a pipelines avançados de processamento de casos legais.

📌 Funcionalidades Principais
🧑‍💼 Gestão de Clientes

Cadastro completo de clientes (PF/PJ)

Edição via modal com HTMX

Exclusão com confirmação

Cards organizados para visualização rápida

⚖️ Gestão de Processos

Cadastro com todos os campos jurídicos importantes

Edição com 12 novos campos (comarca, instância, juiz, valores, etc.)

Associação de advogado responsável

Identificação visual com código hash curto (caso_xxxxxxxx)

📁 Documentos do Processo

Upload de:

PDF

JPEG / PNG

TXT

MP3 / WAV

MP4 / MOV

OCR automático (pdf + imagens)

Extração e armazenamento inteligente

Deleção e atualização dinâmica

🤖 Pipeline de IA (FIRAC, Resumo, Chat, Petição)

Resumo automático do caso

Análise completa no formato FIRAC

Sugerir próximos passos processuais

Identificação de riscos jurídicos

Chat contextual sobre cada caso

Geração de petição inicial baseada em FIRAC + dados do processo

Expansível para outros modelos e análises

📤 Bulk Upload de Processos (CSV)

Upload com validação de estrutura

Preview antes do processamento

Criação em massa via CadastroManager

Envio de notificação por e-mail

Template CSV com 17 campos

🧑‍🤝‍🧑 CRUD de Partes Adversas

Cadastro, edição, exclusão e listagem

Validação automática de processo vinculado

Totalmente integrado ao tenant_id

🛡️ Multi-Tenant Integrado

Cada cliente/usuário trabalha em seu próprio domínio lógico

tenant_id flui automaticamente por todo o backend

📂 Estrutura de Diretórios Recomendada
advocacia-ia-app/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── utils/
│   ├── templates/
│   ├── static/
│   ├── services/
│   ├── auth/
│   ├── routes/
│   │   ├── clientes.py
│   │   ├── processos.py
│   │   ├── advogados.py
│   │   └── …
│   ├── pipeline/
│   │   ├── pipeline.py
│   │   ├── ingestion_handler.py
│   │   ├── case_store.py
│   │   └── …
│   └── ingestion/
│
├── cases/                # Gerado automaticamente
├── migrations/           # Alembic, se usado
├── requirements.txt
├── run.py
├── README.md
├── .env                  # NÃO subir para o GitHub
└── .gitignore

🚀 Instalação e Execução Local
1) Clone o repositório
git clone https://github.com/seu-usuario/advocacia-ia-app.git
cd advocacia-ia-app

2) Crie o ambiente virtual
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

3) Instale as dependências
pip install -r requirements.txt

4) Configure o arquivo .env

Exemplo:

FLASK_ENV=development
SECRET_KEY=uma_chave_segura
DATABASE_URL=postgresql://user:senha@localhost:5432/advocacia
OPENAI_API_KEY=sua_chave
UPLOAD_FOLDER=cases

5) Inicie o servidor
No Windows (PowerShell), recomendamos apontar o Flask para o `manage.py` (isso garante que o `.env` seja carregado):

```powershell
$env:FLASK_APP="manage.py"
flask run -p 5001
```

No Linux/Mac:

```bash
export FLASK_APP=manage.py
flask run -p 5001
```

🏛️ Arquitetura do Projeto
1️⃣ Flask Modular Blueprint

clientes, processos, advogados, partes adversas

Rotas limpas e organizadas

2️⃣ CadastroManager

Abstração completa de banco de dados

Operações CRUD isoladas

Multi-tenant integrado

3️⃣ Pipeline IA

Components:

CaseStore: armazenamento de conteúdo do processo

IngestionHandler: PDF, imagens, áudio, vídeo, texto

Summarizer: resumo + cache

FIRAC Analyzer

Next Steps + Risks analyzer

Chat contextual

Petição Generator

4️⃣ HTMX para UX dinâmica

Formulários modais

Atualizações parciais sem recarregar a página

Experiência muito mais fluida

📤 Deploy na DigitalOcean (Guia Rápido)
📌 1. Criar droplet Ubuntu 22.04

Recomendo:

2GB RAM

1vCPU

50GB SSD

📌 2. Instalar dependências
sudo apt update
sudo apt install python3-pip python3-venv nginx postgresql

📌 3. Criar serviço Gunicorn

Arquivo /etc/systemd/system/advocacia.service:

[Unit]
Description=Gunicorn instance for Advocacia-IA
After=network.target

[Service]
User=root
WorkingDirectory=/root/advocacia-ia-app
ExecStart=/root/advocacia-ia-app/venv/bin/gunicorn -w 4 -b 0.0.0.0:8000 wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target

📌 4. Configurar NGINX

Arquivo /etc/nginx/sites-available/advocacia:

server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

📌 5. Ativar tudo
sudo systemctl enable advocacia
sudo systemctl start advocacia
sudo systemctl restart nginx

🖼️ Screenshots (Adicionar depois)

Crie uma pasta no repositório:

docs/screenshots/


E adicione ao README:

![Tela Clientes](docs/screenshots/clientes.png)
![Painel Processo](docs/screenshots/painel.png)
![Chat do Caso](docs/screenshots/chat.png)

🧪 Roadmap Futuro

🔹 Geração automática de documentos complementares

🔹 Extração automática de dados estruturados de PDFs de sentenças

🔹 API REST completa para integração com outros sistemas

🔹 Dashboard avançado com gráficos e KPIs jurídicos

🔹 Integração com tribunais (TJSP, TJDFT, STJ, etc.)

🔹 Módulo de Jurimetria

💙 Autor

Projeto criado e desenvolvido por Paulo Roberto Souza, 2025.
Com apoio técnico do meu assistente de IA (eu 😄).

📝 Licença

Este projeto é privado.
Não deve ser redistribuído sem autorização.