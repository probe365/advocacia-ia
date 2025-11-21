# tipo_parte Implementation Checklist

## Phase 1: Foundation (✅ COMPLETED)

### Database
- [x] Create Alembic migration file `0004_add_tipo_parte_to_processos.py`
- [x] Add `tipo_parte` column (VARCHAR 50, nullable)
- [x] Create index `ix_processos_tipo_parte`
- [x] Support downgrade (rollback capability)
- [ ] **TODO**: Run migration: `alembic upgrade head`

### Backend - cadastro_manager.py
- [x] Update `save_processo()` method to include `tipo_parte` parameter
- [x] Add `tipo_parte` to INSERT query
- [x] Add `tipo_parte` to UPDATE query
- [x] Support both multi-tenant and single-tenant modes
- [x] Update `bulk_create_processos_from_csv()` docstring
- [x] Add `tipo_parte` column parsing in CSV
- [x] Validate `tipo_parte` against allowed values
- [x] Return error details for invalid `tipo_parte` per line
- [x] Normalize `tipo_parte` to lowercase before saving

### Frontend - bulk_upload_processos.html
- [x] Add `tipo_parte` column to format reference table
- [x] Label as "Opcional"
- [x] List allowed values: autor, reu, terceiro, reclamante, reclamada
- [x] Update CSV example to include `tipo_parte`
- [x] Update preview table to show `tipo_parte` if present

### Utility Functions - tipo_parte_helpers.py
- [x] Create `app/utils/tipo_parte_helpers.py`
- [x] Define `VALID_TIPOS_PARTE` constant
- [x] Define `TIPO_PARTE_LABELS` mapping (English → Portuguese)
- [x] Define `TIPO_PARTE_DESCRIPTIONS` mapping
- [x] Define `TIPO_PARTE_BY_CATEGORY` mapping
- [x] Implement `get_tipo_parte_label()` function
- [x] Implement `get_tipo_parte_description()` function
- [x] Implement `get_tipo_parte_badge_class()` function
- [x] Implement `get_tipo_parte_icon()` function
- [x] Implement `validate_tipo_parte()` function
- [x] Implement `format_tipo_parte_for_display()` function
- [x] Implement `get_tipos_parte_by_category()` function

### Documentation
- [x] Create `TIPO_PARTE_DOCUMENTATION.md` (comprehensive guide)
- [x] Create `TIPO_PARTE_QUICK_REFERENCE.md` (cheat sheet)
- [x] Create `TIPO_PARTE_IMPLEMENTATION_SUMMARY.md` (overview)
- [x] Create `TIPO_PARTE_DIAGRAMS.md` (visual diagrams)
- [x] Create `TIPO_PARTE_CHECKLIST.md` (this file)

---

## Phase 2: User Interface Enhancement (TODO)

### New Process Form
- [ ] Add `tipo_parte` dropdown to `/processos/<id_cliente>/novo` form
- [ ] Populate dropdown with allowed values using `tipo_parte_helpers`
- [ ] Make field optional (not required)
- [ ] Add help text: "Select the role of your client in this case"
- [ ] Show icon and Portuguese label in dropdown
- [ ] Test form submission with and without `tipo_parte`
- [ ] Validate on server-side (backend already supports it)

### Existing Process View
- [ ] Add `tipo_parte` field to process details template
- [ ] Display as badge with icon using `tipo_parte_helpers`
- [ ] Show in read-only mode on initial load
- [ ] Add "Edit" button to modify `tipo_parte`
- [ ] Implement AJAX update without page reload (HTMX)
- [ ] Validate changes on backend

### Process Listing
- [ ] Add `tipo_parte` column to process list (`_lista_processos.html`)
- [ ] Display as small badge
- [ ] Optional: Add sorting by `tipo_parte`
- [ ] Optional: Add filtering by `tipo_parte`

### Search/Filter
- [ ] Add filter option: "Filter by Role"
- [ ] Show checkboxes for each tipo_parte value
- [ ] Update query: `SELECT * FROM processos WHERE tipo_parte IN (...)`
- [ ] Persist filter in session
- [ ] Show active filters in UI

---

## Phase 3: Data Management (TODO)

### Migration of Existing Data
- [ ] Audit existing processes: count with/without `tipo_parte`
- [ ] Decide strategy:
  - [ ] Option A: Leave NULL (no changes needed)
  - [ ] Option B: Inferring from process name/description
  - [ ] Option C: Manual bulk update via CSV
- [ ] If using CSV import:
  - [ ] Create CSV template from existing processes
  - [ ] Use bulk upload feature to populate `tipo_parte`
  - [ ] Verify all processes have `tipo_parte` or confirm NULL is acceptable

### Data Validation
- [ ] Create SQL script to find data quality issues
- [ ] Check for typos or variations: 'AUTOR', 'Autor', 'autor'
- [ ] Verify normalized to lowercase in database
- [ ] Sample 20 processes and verify `tipo_parte` accuracy

### Backup Strategy
- [ ] Backup database before running migration
- [ ] Test migration on staging environment first
- [ ] Document rollback procedure (alembic downgrade)

---

## Phase 4: Testing (TODO)

### Unit Tests
- [ ] Test `validate_tipo_parte()` with all valid values
- [ ] Test `validate_tipo_parte()` with invalid values
- [ ] Test `get_tipo_parte_label()` for all values
- [ ] Test `get_tipo_parte_badge_class()` for CSS classes
- [ ] Test `get_tipo_parte_icon()` for Font Awesome icons
- [ ] Test `get_tipos_parte_by_category()` for filtering

### Integration Tests
- [ ] Test CSV upload with valid `tipo_parte`
- [ ] Test CSV upload with invalid `tipo_parte`
- [ ] Test CSV upload without `tipo_parte` column (backward compat)
- [ ] Test single process creation with `tipo_parte`
- [ ] Test process editing to change `tipo_parte`
- [ ] Test querying by `tipo_parte`

### Database Tests
- [ ] Verify migration creates column
- [ ] Verify index created for `tipo_parte`
- [ ] Test INSERT with `tipo_parte`
- [ ] Test UPDATE existing process to add `tipo_parte`
- [ ] Test migration downgrade (rollback)
- [ ] Performance test on query with WHERE tipo_parte = 'reu'

### UI/UX Tests
- [ ] CSV upload form displays `tipo_parte` column info
- [ ] CSV preview shows `tipo_parte` column
- [ ] Error messages for invalid `tipo_parte` are clear
- [ ] Badge displays correctly in process list
- [ ] Dropdown in new process form works
- [ ] Edit form for `tipo_parte` works smoothly

---

## Phase 5: Analytics & Reporting (TODO)

### Dashboard Integration
- [ ] Create chart: Distribution of processes by `tipo_parte`
- [ ] Show pie chart: % autor vs % reu vs % terceiro
- [ ] Show bar chart: Number of active vs completed by role
- [ ] Create filter: Show only specific `tipo_parte`
- [ ] Show KPIs:
  - [ ] Success rate for autor cases
  - [ ] Success rate for reu cases
  - [ ] Average case duration by role
  - [ ] Cost analysis by role

### Reports
- [ ] Report: "Active Cases by Role"
- [ ] Report: "Case Outcome Analysis by Role"
- [ ] Report: "Workload Distribution"
- [ ] Export reports to PDF

### SQL Queries (Examples)
```sql
-- Processes by role
SELECT tipo_parte, COUNT(*) as count, AVG(duration) 
FROM processos GROUP BY tipo_parte;

-- Success by role
SELECT tipo_parte, COUNT(*) as total, 
       SUM(CASE WHEN outcome='favor' THEN 1 ELSE 0 END) as favorable
FROM processos GROUP BY tipo_parte;

-- Recent autor cases
SELECT * FROM processos 
WHERE tipo_parte = 'autor' 
ORDER BY data_inicio DESC LIMIT 10;
```

---

## Phase 6: AI/Pipeline Integration (TODO - Future)

### FIRAC Customization
- [ ] Read `tipo_parte` in `pipeline.py`
- [ ] Customize FIRAC generation based on role
- [ ] **Autor cases**: Emphasize facts favoring client's position
- [ ] **Reu cases**: Focus on defensive arguments
- [ ] **Labor cases**: Use appropriate labor law context

### Petition Generation
- [ ] Customize petition header based on role
- [ ] Adjust narrative perspective:
  - [ ] Autor: "We seek to recover..."
  - [ ] Reu: "We defend against..."
- [ ] Add role-specific legal arguments
- [ ] Adjust tone and strategy

### Risk Assessment
- [ ] Show different risks for plaintiff vs defendant
- [ ] Highlight exposure for reu cases
- [ ] Highlight enforceability for autor cases
- [ ] Customize recommendations per role

### Example Implementation
```python
# In pipeline.py
def generate_firac(self, id_processo):
    proceso_data = self.get_process_data(id_processo)
    tipo_parte = proceso_data.get('tipo_parte')  # NEW
    
    if tipo_parte == 'autor':
        # Plaintiff strategy
        analysis = self._generate_firac_author_perspective()
    elif tipo_parte == 'reu':
        # Defendant strategy
        analysis = self._generate_firac_defendant_perspective()
    else:
        # Default neutral
        analysis = self._generate_firac_neutral()
    
    return analysis
```

---

## Post-Implementation: Monitoring & Maintenance

### Ongoing Tasks
- [ ] Monitor CSV uploads: success rate, error patterns
- [ ] Check database query performance (index usage)
- [ ] Verify no NULL tipo_parte where unexpected
- [ ] Collect feedback from users
- [ ] Document common issues and solutions

### Optimization
- [ ] If queries slow, add composite index on `(tenant_id, tipo_parte)`
- [ ] Consider caching `tipo_parte` distribution for dashboards
- [ ] Profile slow queries with tipo_parte filtering

### Support & Training
- [ ] Create user guide for CSV format
- [ ] Train team on new field
- [ ] Document best practices
- [ ] Create FAQ

---

## Sign-off & Deployment

### Pre-Deployment Checklist
- [ ] All Phase 1 items complete and tested
- [ ] Database backup created
- [ ] Rollback plan documented
- [ ] Team trained on new feature
- [ ] Documentation reviewed and approved
- [ ] QA sign-off obtained

### Deployment Steps
1. [ ] Stop production application
2. [ ] Backup database: `pg_dump > backup_20251016.sql`
3. [ ] Run migration: `alembic upgrade head`
4. [ ] Verify column created: `SELECT tipo_parte FROM processos LIMIT 1;`
5. [ ] Deploy updated application code
6. [ ] Test CSV upload on production
7. [ ] Monitor error logs for 24 hours
8. [ ] Announce to users

### Rollback Plan (if needed)
1. [ ] Stop application
2. [ ] Restore database: `psql < backup_20251016.sql`
3. [ ] Downgrade migration: `alembic downgrade 0003_create_chat_turns`
4. [ ] Deploy previous application version
5. [ ] Test and verify

---

## Quick Links

| Document | Purpose |
|----------|---------|
| `TIPO_PARTE_DOCUMENTATION.md` | Full technical reference |
| `TIPO_PARTE_QUICK_REFERENCE.md` | Quick cheat sheet |
| `TIPO_PARTE_IMPLEMENTATION_SUMMARY.md` | Implementation overview |
| `TIPO_PARTE_DIAGRAMS.md` | Visual diagrams & flows |
| `app/utils/tipo_parte_helpers.py` | Helper functions (code) |
| `alembic/versions/0004_*.py` | Database migration |

---

## Contact & Questions

- For technical details: Refer to documentation
- For implementation issues: Check error logs
- For feature requests: Update this checklist and Phase section

---

**Last Updated**: October 16, 2025
**Phase 1 Completion**: 100% ✅
**Overall Progress**: Phase 1 Complete, Phase 2-6 Pending
