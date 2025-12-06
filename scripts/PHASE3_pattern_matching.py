#!/usr/bin/env python
"""
Phase 3: Data Migration - Pattern Matching Script
Assigns tipo_parte based on case name patterns.
"""
import os
import re
import psycopg2
from psycopg2.extras import DictCursor

os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_NAME', 'advocacia_ia')
os.environ.setdefault('DB_USER', 'postgres')
os.environ.setdefault('DB_PASSWORD', 'probe365')
os.environ.setdefault('DB_PORT', '5432')

# Patterns for tipo_parte detection
PATTERNS = {
    'autor': [
        r'ação\s+(de|condenatória|declaratória)',
        r'reclamação\s+trabalhista.*\s+(trabalhador|empregado)',
        r'(indenização|reparação|cobrança)\s+de',
        r'demanda.*\s+por',
    ],
    'reu': [
        r'(defesa|ação|resposta)\s+a.*ação',
        r'(contestação|contrariedade)',
        r'defesa\s+(de|administrativo)',
        r'reclamação\s+trabalhista.*\s+(empresa|empregador)',
    ],
    'reclamante': [
        r'reclamação\s+(laboral|trabalhista)\s+(do\s+)?trabalhador',
        r'(demanda|ação)\s+(do\s+)?(funcionário|empregado)',
    ],
    'reclamada': [
        r'reclamação\s+(laboral|trabalhista)\s+(da\s+)?(empresa|empregador)',
        r'(demanda|ação)\s+(da\s+)?(empresa|corporação)',
    ],
    'terceiro': [
        r'(intervenção|interveniência)\s+de\s+terceiro',
        r'assistência\s+(simples|litisconsorcial)',
    ],
}

def detect_tipo_parte(nome_caso: str) -> tuple[str | None, float]:
    """
    Detects tipo_parte from case name using pattern matching.
    Returns (tipo_parte, confidence) where confidence is 0-1.
    """
    if not nome_caso:
        return None, 0.0
    
    nome_lower = nome_caso.lower()
    scores = {}
    
    for tipo, patterns in PATTERNS.items():
        matches = 0
        for pattern in patterns:
            if re.search(pattern, nome_lower):
                matches += 1
        if matches > 0:
            scores[tipo] = matches / len(patterns)
    
    if not scores:
        return None, 0.0
    
    best_tipo = max(scores, key=scores.get)
    confidence = scores[best_tipo]
    
    return best_tipo, confidence

def main():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        port=os.environ.get('DB_PORT')
    )
    
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    print("\n" + "="*80)
    print("TIPO_PARTE PATTERN MATCHING MIGRATION")
    print("="*80)
    
    # Get processes without tipo_parte
    cursor.execute("""
        SELECT id_processo, nome_caso, status FROM processos 
        WHERE tipo_parte IS NULL
        ORDER BY id_processo
    """)
    processes = cursor.fetchall()
    
    print(f"\nFound {len(processes)} processes without tipo_parte")
    
    # Analyze patterns
    results = {
        'high_confidence': [],
        'medium_confidence': [],
        'low_confidence': [],
        'no_match': []
    }
    
    for proc in processes:
        tipo, confidence = detect_tipo_parte(proc['nome_caso'])
        
        if confidence >= 0.8:
            results['high_confidence'].append((proc, tipo, confidence))
        elif confidence >= 0.5:
            results['medium_confidence'].append((proc, tipo, confidence))
        elif confidence > 0:
            results['low_confidence'].append((proc, tipo, confidence))
        else:
            results['no_match'].append(proc)
    
    # Display results
    print("\n📊 Pattern Matching Results:")
    print(f"\n   ✅ HIGH CONFIDENCE (≥80%): {len(results['high_confidence'])}")
    for proc, tipo, conf in results['high_confidence'][:5]:
        print(f"      • {proc['nome_caso'][:40]}... → {tipo} ({conf:.0%})")
    if len(results['high_confidence']) > 5:
        print(f"      ... and {len(results['high_confidence'])-5} more")
    
    print(f"\n   ⚠️  MEDIUM CONFIDENCE (50-80%): {len(results['medium_confidence'])}")
    for proc, tipo, conf in results['medium_confidence'][:3]:
        print(f"      • {proc['nome_caso'][:40]}... → {tipo} ({conf:.0%})")
    
    print(f"\n   ❓ LOW CONFIDENCE (<50%): {len(results['low_confidence'])}")
    print(f"\n   ❌ NO MATCH: {len(results['no_match'])}")
    
    # Option to apply
    print("\n" + "="*80)
    print("💾 Application Options:")
    print("="*80)
    
    high_count = len(results['high_confidence'])
    med_count = len(results['medium_confidence'])
    
    if high_count > 0:
        response = input(f"\nApply HIGH CONFIDENCE assignments ({high_count} processes)? (y/n): ").strip().lower()
        if response == 'y':
            for proc, tipo, conf in results['high_confidence']:
                cursor.execute(
                    "UPDATE processos SET tipo_parte = %s WHERE id_processo = %s",
                    (tipo, proc['id_processo'])
                )
            conn.commit()
            print(f"✅ Applied {high_count} HIGH CONFIDENCE assignments")
    
    if med_count > 0:
        response = input(f"\nApply MEDIUM CONFIDENCE assignments ({med_count} processes)? (y/n): ").strip().lower()
        if response == 'y':
            for proc, tipo, conf in results['medium_confidence']:
                cursor.execute(
                    "UPDATE processos SET tipo_parte = %s WHERE id_processo = %s",
                    (tipo, proc['id_processo'])
                )
            conn.commit()
            print(f"✅ Applied {med_count} MEDIUM CONFIDENCE assignments")
    
    # Verify results
    cursor.execute("SELECT COUNT(*) as count FROM processos WHERE tipo_parte IS NULL")
    remaining = cursor.fetchone()['count']
    
    cursor.execute("""
        SELECT tipo_parte, COUNT(*) as count FROM processos 
        WHERE tipo_parte IS NOT NULL GROUP BY tipo_parte ORDER BY count DESC
    """)
    distribution = cursor.fetchall()
    
    print(f"\n📈 Final Statistics:")
    print(f"   Processes without tipo_parte: {remaining}")
    print(f"   Distribution:")
    for row in distribution:
        print(f"      • {row['tipo_parte']}: {row['count']}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("✅ Pattern matching complete!")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
