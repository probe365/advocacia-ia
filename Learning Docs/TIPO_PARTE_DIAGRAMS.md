```mermaid
graph TD
    A["Cliente/Parte"] -->|"Create Process"| B["Process Registration"]
    B -->|"Identify Role"| C["tipo_parte Field"]
    
    C -->|"autor"| D["Plaintiff<br/>Client sued someone"]
    C -->|"reu"| E["Defendant<br/>Someone sued client"]
    C -->|"terceiro"| F["Third Party<br/>Involved in case"]
    C -->|"reclamante"| G["Claimant (Labor)<br/>Worker complaint"]
    C -->|"reclamada"| H["Respondent (Labor)<br/>Employer complaint"]
    
    B -->|"Upload CSV"| I["Bulk Upload"]
    I -->|"CSV with tipo_parte"| J["Validation"]
    J -->|"Valid"| K["Process Created<br/>tipo_parte Saved"]
    J -->|"Invalid"| L["Error Message<br/>Line Details"]
    
    K -->|"Store in DB"| M["processos Table"]
    M -->|"Column"| N["tipo_parte VARCHAR"]
    N -->|"Indexed"| O["ix_processos_tipo_parte"]
    
    K -->|"Use in UI"| P["Utility Functions"]
    P -->|"Display"| Q["Badge + Icon<br/>Portuguese Label"]
    
    K -->|"Future: AI Analysis"| R["Pipeline Integration"]
    R -->|"Customize by Role"| S["FIRAC Generation"]
    S -->|"Plaintiff Perspective"| T["Strategic Analysis"]
    S -->|"Defendant Perspective"| U["Risk Assessment"]
```

## Data Flow: CSV Upload with tipo_parte

```mermaid
sequenceDiagram
    participant User as User
    participant UI as bulk_upload_processos.html
    participant API as Flask API
    participant Manager as CadastroManager
    participant DB as PostgreSQL
    
    User->>UI: Select CSV file
    UI->>UI: Preview CSV content
    UI->>API: POST /api/bulk-upload
    
    API->>API: Validate file format
    API->>Manager: Call bulk_create_processos_from_csv()
    
    Manager->>Manager: Parse CSV rows
    
    loop For each row
        Manager->>Manager: Extract: nome_caso, tipo_parte, etc.
        Manager->>Manager: Validate tipo_parte
        alt tipo_parte valid or empty
            Manager->>Manager: Create process data
            Manager->>Manager: save_processo()
            Manager->>DB: INSERT INTO processos (tipo_parte)
            DB->>DB: Save with index
        else tipo_parte invalid
            Manager->>Manager: Collect error message
        end
    end
    
    Manager->>API: Return results
    API->>UI: JSON response
    UI->>User: Show success/errors
```

## Entity Relationship: tipo_parte

```mermaid
erDiagram
    CLIENTES ||--o{ PROCESSOS : "has"
    PROCESSOS {
        string id_processo PK
        string id_cliente FK
        string nome_caso
        string numero_cnj
        string status
        string advogado_oab
        string tipo_parte "NEW FIELD"
        date data_inicio
        string tenant_id
    }
    
    ADVOGADOS ||--o{ PROCESSOS : "represents"
    ADVOGADOS {
        string oab PK
        string nome
        string email
        string area_atuacao
    }
    
    TENANTS ||--o{ CLIENTES : "contains"
    TENANTS ||--o{ PROCESSOS : "owns"
```

## Component Interaction: tipo_parte Usage

```mermaid
graph LR
    A["Database<br/>tipo_parte Column"] -->|"Query"| B["CadastroManager<br/>CRUD Methods"]
    B -->|"Read"| C["tipo_parte_helpers<br/>Display Functions"]
    B -->|"Write"| D["bulk_upload_processos.html<br/>CSV Upload Form"]
    
    C -->|"Get Label"| E["UI Components<br/>Badge + Icon"]
    C -->|"Get Icon"| F["Font Awesome<br/>Visualization"]
    C -->|"Validate"| G["Data Validation<br/>Error Messages"]
    
    D -->|"Parse CSV"| B
    D -->|"Preview"| C
    D -->|"Submit"| B
    
    B -->|"Create/Update"| A
    
    A -->|"Filter/Query"| H["Future: Analytics<br/>Reports & Dashboards"]
    A -->|"Analyze"| I["Future: AI Pipeline<br/>FIRAC Generation"]
    I -->|"Customize"| J["Perspective-aware<br/>Risk Assessment"]
```

## State Diagram: tipo_parte Lifecycle

```mermaid
stateDiagram-v2
    [*] --> NotSpecified: New Process
    
    NotSpecified --> Specified: User enters tipo_parte
    Specified --> Validated: Validate against allowed values
    
    Validated --> Valid: Valid value
    Valid --> Saved: Save to database
    Saved --> [*]
    
    Validated --> Invalid: Invalid value
    Invalid --> Error: Return error to user
    Error --> Specified: User corrects
    
    NotSpecified --> Saved: tipo_parte left empty
    
    Saved --> Edited: User edits process
    Edited --> Validated
```

## Value Distribution: Expected uso_parte Patterns

```mermaid
pie title "Typical Case Distribution by tipo_parte"
    "Autor (40%)" : 40
    "Reu (35%)" : 35
    "Terceiro (15%)" : 15
    "Reclamante (7%)" : 7
    "Reclamada (3%)" : 3
```

## Feature Roadmap: tipo_parte Integration

```mermaid
gantt
    title tipo_parte Feature Rollout Timeline
    dateFormat YYYY-MM-DD
    
    section Phase 1
    Database Migration :p1a, 2025-10-16, 1d
    Backend Implementation :p1b, 2025-10-16, 1d
    CSV Upload Support :p1c, 2025-10-16, 1d
    Utility Functions :p1d, 2025-10-16, 1d
    
    section Phase 2 (TODO)
    UI Form Dropdown :p2a, 2025-10-17, 2d
    Process Edit Form :p2b, 2025-10-17, 2d
    Filtering/Search :p2c, 2025-10-18, 2d
    
    section Phase 3 (TODO)
    Reporting Dashboard :p3a, 2025-10-20, 3d
    Analytics Charts :p3b, 2025-10-20, 3d
    
    section Phase 4 (Future)
    AI Pipeline Integration :p4a, 2025-11-01, 5d
    Customized FIRAC :p4b, 2025-11-01, 5d
    Risk Assessment :p4c, 2025-11-05, 3d
```
