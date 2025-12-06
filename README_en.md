1. English README (you can save as README_en.md)
# 🧠 Advocacia e IA — Intelligent Legal Case Management System

**Advocacia e IA** is a modern web platform for law firms, combining client and case management with AI-powered legal analysis.

Built with **Flask + PostgreSQL + OpenAI + Chroma**, it supports workflows such as document ingestion, case analysis (FIRAC), AI-powered chat per case, and automatic draft petition generation.

---

## ✨ Main Features

### 👤 Client Management
- Create and manage clients (individual or corporate)
- Edit clients via Bootstrap modal + HTMX
- Delete with confirmation
- Card-based layout for quick overview

### ⚖️ Case Management
- Full process record with key legal fields:
  - case name, CNJ number, status, party role, lawyer, etc.
- Extended 12+ fields:
  - jurisdiction, court, judge, distribution date, end date, cause value, instance, area, sub-phase, etc.
- Associate a responsible lawyer (OAB)
- Visual identification using a stable short hash (e.g., `caso_a1b2c3d4`)

### 📄 Document Management
Per case, you can upload and index:

- PDF  
- JPG / PNG (images)  
- TXT  
- Audio (MP3 / WAV)  
- Video (MP4 / MOV)  

Features:
- OCR for PDFs and images (via OpenAI / ingestion pipeline)
- Automatic text extraction and chunking
- Storage in vector database (Chroma)
- Delete documents by filename and update vector store
- Separate stores for:
  - **case-specific documents**
  - **global knowledge base (KB)**
  - **jurisprudence / ementas KB**

### 🤖 AI Pipeline (Summary, FIRAC, Chat, Petitions)

The `Pipeline` orchestrates several AI capabilities:

- **Case Summarization**
  - Map-Reduce style summarization using LangChain
  - Summary caching based on case document digest

- **FIRAC Analysis**
  - Generates structured FIRAC (Facts, Issue, Rules, Application, Conclusion)  
  - JSON-based structure with validators and fallbacks  
  - Robust text parsing when JSON is not available  
  - Can be exported to PDF/TXT

- **Risk Analysis**
  - Identifies legal and procedural risks based on case context
  - Outputs prioritized list of risks with probability, impact, mitigation

- **Next Steps Suggestions**
  - Strategic recommendations:
    - Immediate actions
    - Evidence and proof collection
    - Appeals / resources
    - Negotiation / settlement
    - Client communication

- **Case Chat (per process)**
  - Chat interface bound to a specific case
  - Uses case documents + global KB, depending on selected scope
  - Chat history persisted in user session
  - Built using LangChain tools + OpenAI functions

- **Draft Petition Generation**
  - Uses FIRAC + UI inputs (court, parties, value, etc.)
  - Generates a structured Portuguese draft petition
  - Export options:
    - PDF (via FPDF)
    - DOCX (via python-docx)

### 📥 Bulk Upload of Cases (CSV)

- Drag-and-drop CSV upload for batch creation of cases
- CSV validation:
  - UTF-8
  - required columns
- Preview before commit
- Uses `CadastroManager.bulk_create_processos_from_csv`
- Email notification endpoint (SMTP-based) for upload summary

Includes a **downloadable template** with 17 fields:
- core fields: `nome_caso`, `numero_cnj`, `status`, `advogado_oab`, `tipo_parte`
- plus: jurisdiction, court, judge, dates, values, notes, etc.

### 👥 Adverse Parties CRUD

- Full CRUD for adverse parties linked to each process
- API endpoints:
  - list, get, create, update, delete
- All operations respect:
  - `tenant_id`
  - `id_processo` ownership

### 🏢 Multi-Tenant Ready

- `tenant_id` flows via Flask `g.tenant_id`
- `CadastroManager` and related services are tenant-aware
- All main operations (clients, cases, adverse parties, bulk uploads) respect tenant boundaries

---

## 📂 Recommended Project Structure

```bash
advocacia-ia-app/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── clientes.html
│   │   ├── processo.html
│   │   ├── _form_cliente.html
│   │   ├── _cards_cliente.html
│   │   ├── _lista_processos.html
│   │   ├── _lista_documentos.html
│   │   ├── _conversa_chat.html
│   │   └── ...
│   ├── static/
│   ├── routes/
│   │   ├── clientes.py
│   │   ├── processos.py
│   │   └── ...
│   ├── services/
│   │   ├── cadastro_service.py
│   │   └── ...
│   ├── pipeline/
│   │   ├── pipeline.py
│   │   ├── ingestion_module.py
│   │   ├── analysis_module.py
│   │   ├── petition_module.py
│   │   └── ...
│   └── utils/
│
├── cases/                # auto-generated (per case: vectorstores, uploads, exports)
├── requirements.txt
├── run.py                # Flask app entrypoint
├── README.md
├── README_en.md
├── .env                  # local env vars (DO NOT commit)
└── .gitignore

🔧 Installation (Local Development)
1) Clone the repository
git clone https://github.com/your-user/advocacia-ia-app.git
cd advocacia-ia-app

2) Create and activate virtualenv
python -m venv venv
# Linux / Mac
source venv/bin/activate
# Windows
venv\Scripts\activate

3) Install dependencies
pip install -r requirements.txt

4) Configure environment variables

Create a .env file in the project root, for example:

FLASK_ENV=development
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://user:password@localhost:5432/advocacia
OPENAI_API_KEY=your_openai_key
UPLOAD_FOLDER=cases

SMTP_HOST=smtp.yourserver.com
SMTP_PORT=587
SMTP_USER=your_user
SMTP_PASSWORD=your_password
EMAIL_FROM=noreply@advocacia-ia.com

5) Run the app
flask run


Then open:

http://127.0.0.1:5000

🚀 Deployment (DigitalOcean + Gunicorn + NGINX)

High-level steps:

Create a Droplet (Ubuntu 22.04)

Install system deps

sudo apt update
sudo apt install python3-pip python3-venv nginx postgresql


Clone the repo to /var/www/advocacia-ia-app

Create virtualenv and install requirements

Configure Gunicorn service (systemd unit)

Example /etc/systemd/system/advocacia-ia.service:

[Unit]
Description=Gunicorn for Advocacia e IA
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/advocacia-ia-app
ExecStart=/var/www/advocacia-ia-app/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 run:app
Restart=always

[Install]
WantedBy=multi-user.target


Configure NGINX reverse proxy

Example /etc/nginx/sites-available/advocacia-ia:

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}


Enable and restart:

sudo ln -s /etc/nginx/sites-available/advocacia-ia /etc/nginx/sites-enabled/advocacia-ia
sudo systemctl restart nginx
sudo systemctl enable advocacia-ia
sudo systemctl start advocacia-ia

📸 Screenshots (Optional)

Create a folder:

docs/screenshots/


And reference them in the README:

![Clients Screen](docs/screenshots/clients.png)
![Case Panel](docs/screenshots/case_panel.png)
![Case Chat](docs/screenshots/case_chat.png)

🧭 Roadmap (Next Steps)

Automatic extraction of structured data from judgments / decisions

Full REST API for external integrations

Advanced dashboards (KPIs, charts, legal analytics)

Integrations with Brazilian court systems (TJSP, TJDFT, STJ, etc.)

Jurimetrics module

👤 Author

Created by Paulo Roberto Souza (2025)
Private project – not for redistribution without permission.