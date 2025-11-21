# tipo_parte - Quick Reference Card

## What is tipo_parte?
It identifies the **role** of the client in a legal case:
- **autor** = Plaintiff (brought the lawsuit)
- **reu** = Defendant (being sued)
- **terceiro** = Third party (involved but not main parties)
- **reclamante** = Claimant (labor cases - worker)
- **reclamada** = Respondent (labor cases - employer)

## Where to Use It?

### 1. CSV Bulk Upload ✅
Add an optional 5th column to your CSV:
```csv
nome_caso,numero_cnj,status,advogado_oab,tipo_parte
"Case Name",123456789012345678,ATIVO,SP123456,autor
```

### 2. Single Process Creation (TO-DO)
When creating one process, select from dropdown.

### 3. Process Editing (TO-DO)
Can edit `tipo_parte` in process details.

## CSV Examples

### Example 1: Client as Plaintiff
```csv
nome_caso,tipo_parte
"Debt Collection Against Company X",autor
```
**Meaning**: Your client is suing Company X

### Example 2: Client as Defendant
```csv
nome_caso,tipo_parte
"Employment Dispute",reu
```
**Meaning**: Your client is being sued

### Example 3: Labor Case
```csv
nome_caso,tipo_parte
"Wrongful Dismissal Claim",reclamante
```
**Meaning**: Your client (worker) filed complaint against employer

## Validation Rules

| Value | Valid | Notes |
|-------|-------|-------|
| `autor` | ✅ | Civil cases |
| `reu` | ✅ | Civil cases |
| `terceiro` | ✅ | Any case |
| `reclamante` | ✅ | Labor cases |
| `reclamada` | ✅ | Labor cases |
| `AUTOR` | ✅ | Case-insensitive |
| `invalid_value` | ❌ | Error! |
| Empty/blank | ✅ | Optional |

## How to Access tipo_parte in Code

### Python
```python
from app.utils.tipo_parte_helpers import *

# Get Portuguese label
get_tipo_parte_label('reu')  # 'Réu'

# Get description
get_tipo_parte_description('autor')

# Get Bootstrap badge class
get_tipo_parte_badge_class('reclamante')  # 'badge-info'

# Get Font Awesome icon
get_tipo_parte_icon('reu')  # 'fa-shield-alt'

# Format for HTML template
format_tipo_parte_for_display('autor')
# Returns: <span class="badge badge-primary"><i class="fas fa-gavel"></i> Autor</span>

# Validate
validate_tipo_parte('reclamada')  # True
validate_tipo_parte('xyz')  # False
```

### Jinja2 Templates
```html
<!-- Display with badge and icon -->
{{ tipo_parte_helpers.format_tipo_parte_for_display(processo.tipo_parte) | safe }}

<!-- Or manually -->
<span class="badge {{ tipo_parte_helpers.get_tipo_parte_badge_class(processo.tipo_parte) }}">
    <i class="fas {{ tipo_parte_helpers.get_tipo_parte_icon(processo.tipo_parte) }}"></i>
    {{ tipo_parte_helpers.get_tipo_parte_label(processo.tipo_parte) }}
</span>
```

### SQL
```sql
-- Find all processes where client is plaintiff
SELECT * FROM processos WHERE tipo_parte = 'autor';

-- Find all defendant cases
SELECT * FROM processos WHERE tipo_parte = 'reu';

-- Find all labor cases
SELECT * FROM processos WHERE tipo_parte IN ('reclamante', 'reclamada');

-- Count by role
SELECT tipo_parte, COUNT(*) FROM processos GROUP BY tipo_parte;
```

## Database

### Column Details
- **Table**: `processos`
- **Column**: `tipo_parte`
- **Type**: VARCHAR(50)
- **Nullable**: Yes (optional)
- **Index**: `ix_processos_tipo_parte`

### Migration
```bash
# Apply migration
alembic upgrade head

# Verify
SELECT * FROM processos LIMIT 5;  # Should show tipo_parte column
```

## Error Messages

### Error 1: Invalid tipo_parte in CSV
```
Linha 5: tipo_parte inválido. Valores válidos: autor, reu, terceiro, reclamante, reclamada
```
**Fix**: Check spelling, ensure lowercase, use only from valid list

### Error 2: tipo_parte not found
```
Erro: 'tipo_parte' column not found
```
**Fix**: Run `alembic upgrade head` to create column

## Features Using tipo_parte (Future)

- 🔄 Filter processes by role
- 📊 Dashboard showing distribution (author vs defendant)
- 🤖 AI analysis customized per role
- ⚖️ Risk assessment different for plaintiff vs defendant
- 📄 Petitions generated from client's perspective
- 📈 Statistics & reporting by type

## Files Modified/Created

| File | Status | Purpose |
|------|--------|---------|
| `alembic/versions/0004_add_tipo_parte_to_processos.py` | ✅ CREATED | Database migration |
| `cadastro_manager.py` | ✅ UPDATED | Backend method support |
| `templates/bulk_upload_processos.html` | ✅ UPDATED | CSV format docs + example |
| `app/utils/tipo_parte_helpers.py` | ✅ CREATED | Utility functions |
| `TIPO_PARTE_DOCUMENTATION.md` | ✅ CREATED | Full documentation |

## Testing Checklist

- [ ] Migration runs without errors: `alembic upgrade head`
- [ ] CSV with tipo_parte uploads successfully
- [ ] CSV with invalid tipo_parte shows error
- [ ] CSV without tipo_parte works (backward compat)
- [ ] Helper functions return correct values
- [ ] Database column created and indexed

## Need Help?

1. **How do I use tipo_parte in CSV?**
   → See "CSV Examples" section above

2. **What are valid values?**
   → See "Validation Rules" table

3. **How to query by tipo_parte?**
   → See "SQL" examples

4. **How to display in templates?**
   → See "Jinja2 Templates" section

5. **Full technical details?**
   → Read `TIPO_PARTE_DOCUMENTATION.md`
