#!/usr/bin/env python
"""
Phase 3: Data Migration - Audit Script
Identifies existing processes needing tipo_parte assignment and provides strategies.
"""
import os
import psycopg2
from psycopg2.extras import DictCursor
from collections import defaultdict

os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_NAME', 'advocacia_ia')
os.environ.setdefault('DB_USER', 'postgres')
os.environ.setdefault('DB_PASSWORD', 'probe365')
os.environ.setdefault('DB_PORT', '5432')

conn = psycopg2.connect(
    host=os.environ.get('DB_HOST'),
    database=os.environ.get('DB_NAME'),
    user=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASSWORD'),
    port=os.environ.get('DB_PORT')
)

cursor = conn.cursor(cursor_factory=DictCursor)

print("\n" + "="*80)
print("TIPO_PARTE DATA MIGRATION AUDIT REPORT")
print("="*80)

# 1. Count processes by tipo_parte status
print("\n📊 Overall Statistics:")
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN tipo_parte IS NOT NULL THEN 1 END) as with_tipo_parte,
        COUNT(CASE WHEN tipo_parte IS NULL THEN 1 END) as without_tipo_parte
    FROM processos
""")
stats = cursor.fetchone()
total = stats['total']
with_tipo_parte = stats['with_tipo_parte']
without_tipo_parte = stats['without_tipo_parte']

print(f"   Total processes: {total}")
print(f"   ✓ With tipo_parte: {with_tipo_parte} ({with_tipo_parte*100//total if total else 0}%)")
print(f"   ✗ Without tipo_parte: {without_tipo_parte} ({without_tipo_parte*100//total if total else 0}%)")

# 2. Distribution of tipo_parte values
print("\n📈 Distribution of tipo_parte values:")
cursor.execute("""
    SELECT tipo_parte, COUNT(*) as count
    FROM processos
    WHERE tipo_parte IS NOT NULL
    GROUP BY tipo_parte
    ORDER BY count DESC
""")
distribution = cursor.fetchall()
for row in distribution:
    print(f"   • {row['tipo_parte']}: {row['count']}")

# 3. Processes by status (to assess data quality)
print("\n🔄 Processes by status:")
cursor.execute("""
    SELECT status, COUNT(*) as count
    FROM processos
    GROUP BY status
    ORDER BY count DESC
""")
status_dist = cursor.fetchall()
for row in status_dist:
    print(f"   • {row['status']}: {row['count']}")

# 4. Processes without tipo_parte - sample names for pattern detection
print("\n🔍 Sample of processes WITHOUT tipo_parte (for pattern analysis):")
cursor.execute("""
    SELECT id_processo, nome_caso, status, data_inicio
    FROM processos
    WHERE tipo_parte IS NULL
    ORDER BY data_inicio DESC
    LIMIT 10
""")
samples = cursor.fetchall()
if samples:
    for idx, row in enumerate(samples, 1):
        print(f"   {idx}. {row['nome_caso']} (Status: {row['status']})")
else:
    print("   ✓ All processes have tipo_parte assigned!")

# 5. Processes per client (to understand data organization)
print("\n👥 Processes per client (top 10):")
cursor.execute("""
    SELECT id_cliente, COUNT(*) as count, 
           COUNT(CASE WHEN tipo_parte IS NOT NULL THEN 1 END) as with_tipo_parte
    FROM processos
    GROUP BY id_cliente
    ORDER BY count DESC
    LIMIT 10
""")
client_dist = cursor.fetchall()
for row in client_dist:
    completion = (row['with_tipo_parte']*100//row['count']) if row['count'] else 0
    print(f"   • Client {row['id_cliente'][:8]}...: {row['with_tipo_parte']}/{row['count']} ({completion}%)")

# 6. Strategy recommendations
print("\n💡 Migration Strategies:")
print("""
   Option A: LEAVE AS NULL (Do Nothing)
      ✓ Pros: No risk of data corruption
      ✓ Pros: Backward compatible
      ✗ Cons: Users must manually assign tipo_parte to existing cases
      ⏱️  Effort: 0 minutes
      
   Option B: INTELLIGENT PATTERN MATCHING
      ✓ Pros: Assigns tipo_parte based on case name patterns
      ✓ Pros: Reduces manual work
      ✗ Cons: May have false positives (e.g., "Defesa de...")
      ⏱️  Effort: 30 minutes (create script, test, verify)
      Pattern Examples:
         - "ação de ..." → "autor"
         - "defesa de ..." → "reu"
         - "reclamação ..." → "reclamante"
         - "reclamada em ..." → "reclamada"
      
   Option C: BULK ASSIGNMENT (Manual Review)
      ✓ Pros: Team reviews and assigns manually
      ✓ Pros: 100% accurate
      ✗ Cons: Time-intensive
      ⏱️  Effort: {:.0f} minutes (depends on total processes)
      Recommended: For critical/important cases only
      
   Option D: HYBRID (Pattern + Manual Review)
      ✓ Pros: Combines automation with verification
      ✓ Pros: Most accurate and efficient
      ✗ Cons: Requires coordination
      ⏱️  Effort: 60 minutes
      Process: 
         1. Run pattern matching on all processes
         2. Flag low-confidence matches for review
         3. Team reviews flagged items
         4. Update in bulk
""".format(without_tipo_parte * 5 // 60))  # Estimate 5 min per process

# 7. Next steps
print("\n🚀 Next Steps:")
print("""
   1. Decide on migration strategy (A, B, C, or D)
   2. If strategy B or D: Run pattern_matching_script.py
   3. If strategy C or D: Use bulk_update_tipo_parte.py for manual assignment
   4. Verify data quality: SELECT COUNT(*) ... WHERE tipo_parte IS NULL
   5. Update UI to show tipo_parte in process list (already done!)
   6. Proceed to Phase 4: Testing
""")

# 8. Export CSV for manual review (if needed)
print("\n📥 Export options:")
print("""
   To export processes without tipo_parte for manual review:
   
   python export_processes_for_review.py
   
   This will create: processes_for_review_TIMESTAMP.csv
""")

cursor.close()
conn.close()

print("\n" + "="*80)
print("✅ Audit complete! Review the options above and proceed accordingly.")
print("="*80 + "\n")
