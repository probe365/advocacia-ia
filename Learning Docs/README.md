# Advocacia IA Platform

Modern Flask-based multi-tenant law practice assistant with AI chat, document ingestion, and process management.

## Features
- Flask app factory + blueprints (`clientes`, `processos`, `documentos`, `chat`, `auth`, `health`, `metrics`).
- Multi-tenant ready (optional `tenant_id` filtering).
- PostgreSQL via raw SQL + Alembic migrations.
- AI integration (LangChain + OpenAI + Chroma vector store).
- Chat history persisted (`chat_turns`).
- HTMX-enhanced UI fragments for fast interactions.
- Docker multi-stage image + `docker-compose` (app + Postgres).
- Makefile for common tasks.
- Separate `requirements.txt` (runtime) and `requirements-dev.txt`.

## Quick Start (Local)
```powershell
# 1. Create virtual env
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install deps
pip install -r requirements.txt -r requirements-dev.txt

# 3. Copy env template
Copy-Item .env.example .env
# Edit .env with real secrets (OPENAI_API_KEY, FLASK_SECRET_KEY)

# 4. Initialize DB (Postgres running)
$env:FLASK_APP="manage.py"; flask db upgrade

# 5. Run dev server
$env:FLASK_APP="manage.py"; flask run -p 5001
```
Visit: http://localhost:5001/

### One-Step Dev Startup
Use the helper script (creates venv, installs deps, applies migrations, runs server):
```powershell
scripts\dev_up.ps1
```
Add `-ForceRecreate` to rebuild the virtual environment.

### Teardown / Cleanup
Stop and clean resources:
```powershell
# Stop Docker stack + remove volumes + remove venv + purge data
scripts\teardown.ps1 -Docker -RemoveVenv -PurgeData

# Only remove venv
scripts\teardown.ps1 -RemoveVenv

# Only stop Docker containers (keep volumes)
scripts\teardown.ps1 -Docker
```

## With Docker Compose
```powershell
docker compose up -d --build
```
Logs:
```powershell
docker compose logs -f app
```

## Makefile Targets
```text
make install          # runtime deps
make install-dev      # + dev deps
make run              # flask dev server
make dev              # gunicorn
make upgrade          # migrations
make revision msg=desc
make docker-build TAG=dev
make docker-run TAG=dev
```

## Environment Variables
See `.env.example` for full list. Key ones:
- FLASK_SECRET_KEY: session security.
- DB_*: PostgreSQL connection.
- MULTI_TENANT=1 to enable tenant scoping.
- OPENAI_API_KEY for AI features.
- CHROMA_PERSIST_DIR path for vector store persistence.

## Database / Migrations
Alembic revisions live in `alembic/versions/`.
To create a new revision:
```powershell
$env:FLASK_APP="manage.py"; flask db revision --autogenerate -m "desc"
$env:FLASK_APP="manage.py"; flask db upgrade
```

## Architecture Overview
```
app/
  __init__.py          # create_app factory
  blueprints/          # route groupings
  middleware.py        # tenant + metrics hooks
  metrics.py           # /metrics endpoint
  services/            # business service layer
cadastro_manager.py     # data access (raw SQL)
manage.py               # Alembic integration
wsgi.py                 # production entry
```

### System Architecture (Core)
```mermaid
flowchart TD
  A[Browser User] --> B[Flask App\nGunicorn wsgi:app]
  subgraph App_Layer
    B --> C[Blueprints\nclientes / processos / documentos / chat]
    C --> S[Service Layer\nCadastroService]
    S --> M[(PostgreSQL)]
    C --> P[AI Pipeline\nLangChain + OpenAI]
    P --> V[(Chroma Store)]
    V --> FS[(Embeddings Disk)]
    S --> CH[(chat_turns)]
  end
  M <-->|Alembic| D[alembic/versions]
  B --> MET[/metrics endpoint/]
  B --> L[Flask-Login]
```

### Expanded Architecture (Beta)
```mermaid
flowchart TD
  %% Beta architecture diagram with extended components & refined shapes
  subgraph Client
    U(("User\nBrowser / HTMX"))
  end
  subgraph WebTier
    GW{{"Reverse Proxy /\nLoad Balancer"}}
    APP(["Flask App\nwsgi:app"])
  end
  subgraph AppLayer[Application Layer]
    BP[["Blueprints\nclientes / processos / documentos / chat / auth / metrics"]]
    SRV["Service Layer\nCadastroService"]
    AUTH(("Auth / Session"))
    MT{{"Multi-Tenant\nMiddleware"}}
    VAL>"Input Validation"]
    LOG["Structured Logging"]
    METR(["Metrics Exporter"])
  end
  subgraph AIPipeline[AI & RAG Pipeline]
    LC[["LangChain\nOrchestrator"]]
    EMB(["Embedding Model"])
    VDB[("Chroma Vector Store")]
    RETR{"Retriever"}
    LLM(("OpenAI API"))
  end
  subgraph Data
    PG[("PostgreSQL")]
    TBL[("chat_turns &\nDomain Tables")]
    MIG[["alembic/versions"]]
    FS[("Embeddings Disk Volume")]
  end
  subgraph Ops[Operations]
    CFG>".env / Feature Flags"]
    CTNR(["Docker / Compose"])
    MIGT(("Alembic CLI"))
  end
  U --> GW --> APP
  APP --> BP --> SRV --> PG
  SRV --> TBL
  MIG -. schema .-> PG
  MIG -. versioned .-> TBL
  APP --> AUTH
  APP --> MT
  APP --> LOG
  APP --> METR
  BP --> LC
  LC --> EMB --> VDB
  VDB --> FS
  LC --> RETR --> LLM
  LLM --> LC
  CFG --> APP
  CTNR --> APP
  MIGT --> MIG
  LOG --> FS
  classDef data fill:#eef,stroke:#336;
  classDef ai fill:#efe,stroke:#363;
  classDef ops fill:#fee,stroke:#633;
  classDef app fill:#f5f9ff,stroke:#357;
  class PG,TBL,MIG,FS data
  class LC,EMB,VDB,RETR,LLM ai
  class CFG,CTNR,MIGT ops
  class APP,BP,SRV,AUTH,MT,VAL,LOG,METR app
```

### Deployment Diagram
```mermaid
C4Deployment
  title Deployment Diagram - AI Legal Platform (Docker Compose)
  Deployment_Node(user_dev, "User Device", "Browser / HTMX") {
    Deployment_Node(browser, "Web Browser", "Chrome / Firefox / Edge") {
      Container(web_ui, "HTMX Frontend", "HTML/JS", "Dynamic partial updates & form submissions")
    }
  }
  Deployment_Node(edge, "Reverse Proxy", "Nginx / Traefik", "TLS termination, routing, compression") {
    Container(reverse_proxy, "Reverse Proxy", "Nginx/Traefik", "TLS, routing, compression, static caching")
  }
  Deployment_Node(docker_host, "Docker Host", "Linux / WSL2", "Compose Network: app, db, chroma") {
    Deployment_Node(app_ctr, "app:latest x2", "Python 3.11 + Gunicorn", "Flask API + LangChain orchestration") {
      Container(api_app, "Flask Application", "Gunicorn wsgi:app", "CRUD, Chat, RAG, metrics")
    }
    Deployment_Node(db_ctr, "postgres:16", "PostgreSQL", "Transactional & chat turns") {
      ContainerDb(pg_db, "Primary DB", "PostgreSQL", "Clientes, Processos, Documentos, chat_turns")
    }
    Deployment_Node(chroma_ctr, "chroma:latest", "Chroma Vector Store", "Embeddings & index") {
      Container(chroma, "Chroma Service", "Python", "Vector embeddings for RAG")
    }
    Deployment_Node(migrate_job, "alembic-migrate", "Alembic CLI", "Schema migrations") {
      Container(migrate_task, "Alembic Runner", "Python", "Versioned DDL updates")
    }
  }
  Deployment_Node(openai_edge, "OpenAI API", "Managed SaaS", "LLM / Embedding inference") {
    Container_Ext(openai_api, "OpenAI", "HTTPS", "ChatCompletion / Embeddings endpoints")
  }
  Rel(web_ui, reverse_proxy, "HTTP(S) requests", "HTTPS")
  Rel(reverse_proxy, api_app, "Routes / forwards", "HTTP")
  Rel(web_ui, api_app, "(Dev) Direct calls", "HTTP")
  Rel(api_app, pg_db, "SQL queries", "psycopg2 / 5432")
  Rel(api_app, chroma, "Vector similarity / CRUD", "HTTP / gRPC")
  Rel(api_app, openai_api, "LLM & Embedding calls", "HTTPS")
  Rel(migrate_task, pg_db, "Apply migrations", "SQL DDL")
```

### Component Diagram
```mermaid
C4Component
  title Component Diagram - Flask AI Legal Platform
  Person(user, "User", "Lawyer / Staff interacting via browser")
  Container_Boundary(app, "Flask Application", "Python / Flask 3 + Gunicorn") {
    Component(bp_clientes, "Clientes Blueprint", "Flask Blueprint", "Client CRUD UI & API")
    Component(bp_processos, "Processos Blueprint", "Flask Blueprint", "Process management UI & API")
    Component(bp_documentos, "Documentos Blueprint", "Flask Blueprint", "Upload & list documents")
    Component(bp_chat, "Chat Blueprint", "Flask Blueprint", "Chat endpoints & HTMX fragments")
    Component(bp_auth, "Auth Blueprint", "Flask Blueprint", "Login / session handling")
    Component(bp_metrics, "Metrics Endpoint", "Flask Route", "Exposes Prometheus metrics")
    Component(mw_tenant, "Tenant Middleware", "WSGI Middleware", "Inject tenant_id from header / default")
    Component(mw_metrics, "Metrics Middleware", "WSGI Middleware", "Latency / request counting")
    Component(service_layer, "CadastroService", "Service Layer", "Business logic orchestration")
    Component(data_access, "CadastroManager", "Data Access (raw SQL)", "CRUD + chat_turn persistence")
    Component(ingestion, "Ingestion Module", "Pipeline", "Text extraction + chunking + embedding queue")
    Component(chat_logic, "Chat Pipeline", "LangChain Orchestrator", "Context retrieval + LLM completion")
    Component(vector_client, "Vector Store Client", "Chroma Wrapper", "Similarity search & upserts")
    Component(openai_client, "OpenAI Client", "API Adapter", "LLM + Embeddings calls")
    Component(authn, "Auth Session", "Flask-Login", "User session & identity")
  }
  SystemDb(db, "PostgreSQL", "Relational DB", "Domain tables + chat_turns")
  ContainerDb_Ext(chroma, "Chroma Vector Store", "Chroma", "Persistent embeddings & metadata")
  System_Ext(openai, "OpenAI API", "LLM / Embeddings", "External SaaS")
  Rel(user, bp_clientes, "Uses", "HTTPS")
  Rel(user, bp_processos, "Uses", "HTTPS")
  Rel(user, bp_documentos, "Uploads", "HTTPS")
  Rel(user, bp_chat, "Chats", "HTTPS")
  Rel(user, bp_auth, "Authenticates", "HTTPS")
  Rel(bp_chat, chat_logic, "Invoke chat flow")
  Rel(chat_logic, vector_client, "Similarity search")
  Rel(vector_client, chroma, "Query / upsert vectors")
  Rel(chat_logic, openai_client, "Prompt + context")
  Rel(openai_client, openai, "LLM & embedding requests")
  Rel(chat_logic, data_access, "Persist chat_turns")
  Rel(bp_documentos, ingestion, "Trigger ingestion")
  Rel(ingestion, openai_client, "Embed chunks")
  Rel(ingestion, vector_client, "Store embeddings")
  Rel(ingestion, data_access, "Record metadata")
  Rel(service_layer, data_access, "SQL ops")
  Rel(data_access, db, "SQL queries")
  Rel(bp_auth, authn, "Session mgmt")
  Rel(bp_metrics, mw_metrics, "Exposure of collected metrics")
  Rel(mw_tenant, service_layer, "Tenant context propagation")
```

### Chat Request Sequence (RAG Flow)
```mermaid
sequenceDiagram
  title Chat Request with RAG Retrieval
  autonumber
  participant U as User Browser (HTMX)
  participant F as Flask App
  participant SVC as Service Layer
  participant V as Chroma Vector Store
  participant OAI as OpenAI API
  participant DB as PostgreSQL
  U->>F: POST /chat (prompt)
  activate F
  F->>SVC: validate & route
  activate SVC
  SVC->>DB: INSERT chat_turn (user message)
  DB-->>SVC: ack
  SVC->>V: similarity search (k vectors)
  V-->>SVC: top-k docs
  SVC->>OAI: prompt + retrieved context
  OAI-->>SVC: model completion
  SVC->>DB: INSERT chat_turn (assistant reply)
  DB-->>SVC: ack
  SVC-->>F: response payload (HTML fragment)
  deactivate SVC
  F-->>U: HTMX swap (updated chat window)
  deactivate F
  Note over SVC,V: Embeddings precomputed during ingestion
  Note over F,SVC: Multi-tenant ID added to queries if enabled
```

### Document Ingestion Sequence
```mermaid
sequenceDiagram
  title Document Ingestion & Embedding Flow
  autonumber
  participant U as User Browser (HTMX)
  participant F as Flask App
  participant ING as Ingestion Service
  participant TXT as Text Extractor
  participant EMB as Embedding Model (OpenAI)
  participant V as Chroma Vector Store
  participant DB as PostgreSQL
  U->>F: POST /documentos/upload (file)
  activate F
  F->>ING: initiate ingestion(job_id, tenant)
  activate ING
  ING->>TXT: extract_text(file)
  TXT-->>ING: raw text
  ING->>DB: INSERT document metadata (filename, size, tenant)
  DB-->>ING: id
  loop Chunking
    ING->>ING: split text into chunks
  end
  ING->>EMB: embed(batch of chunks)
  EMB-->>ING: vectors[]
  ING->>V: upsert(chunks, vectors, metadata)
  V-->>ING: ack
  ING->>DB: UPDATE document status = 'indexed'
  DB-->>ING: ack
  ING-->>F: ingestion result (doc_id)
  deactivate ING
  F-->>U: Upload success + indexed flag
  deactivate F
  Note over ING,TXT: Supports PDFs / text assuming local parsers
  Note over ING,V: Metadata includes tenant_id & process reference
  Note over ING,EMB: OpenAI API key required
```

## AI Pipeline (High-Level)
1. Documents uploaded -> processed & embedded.
2. Stored in Chroma vector store under case context.
3. Chat queries retrieve context via similarity search.
4. LangChain model (OpenAI) generates responses.
5. Exchanges persisted to `chat_turns`.

## Multi-Tenancy
Enable by setting `MULTI_TENANT=1`. All CRUD queries add `tenant_id` filters; default tenant from `DEFAULT_TENANT_ID` or request header (middleware). Plan further isolation with schema-level or row‑level security if needed.

## Development Notes
- Runtime table creation removed: rely solely on Alembic migrations.
- Keep dependency list lean; reintroduce optional libs only if used.
- Use `requirements-dev.txt` for tooling (mypy, pytest).

## Testing
```powershell
pytest -q
```
Add tests under a `tests/` directory (not yet created).

## Production Recommendations
- Use a stronger WAF/Reverse proxy (nginx/traefik) in front of Gunicorn.
- Set `FLASK_ENV=production` and a strong `FLASK_SECRET_KEY`.
- Rotate API keys and secrets via secret manager.
- Enable structured logging and metrics scraping (/metrics).

## LICENSE
Proprietary (adjust as needed).

---
Feel free to request more detailed module docs or a system diagram.
