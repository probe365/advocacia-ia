#!/usr/bin/env python
"""
Phase 5: Analytics - Dashboard Queries for tipo_parte
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

class TipoParteAnalytics:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.environ.get('DB_HOST'),
            database=os.environ.get('DB_NAME'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            port=os.environ.get('DB_PORT')
        )
        self.cursor = self.conn.cursor(cursor_factory=DictCursor)
    
    def close(self):
        """Close database connection"""
        self.cursor.close()
        self.conn.close()
    
    def get_distribution_by_role(self):
        """Query: Distribution of processes by tipo_parte"""
        self.cursor.execute("""
            SELECT 
                tipo_parte,
                COUNT(*) as count,
                ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM processos
            WHERE tipo_parte IS NOT NULL
            GROUP BY tipo_parte
            ORDER BY count DESC
        """)
        return self.cursor.fetchall()
    
    def get_status_by_role(self):
        """Query: Process status distribution by role"""
        self.cursor.execute("""
            SELECT 
                tipo_parte,
                status,
                COUNT(*) as count
            FROM processos
            WHERE tipo_parte IS NOT NULL
            GROUP BY tipo_parte, status
            ORDER BY tipo_parte, count DESC
        """)
        return self.cursor.fetchall()
    
    def get_advogados_per_role(self):
        """Query: Advogados by tipo_parte"""
        self.cursor.execute("""
            SELECT 
                tipo_parte,
                COUNT(DISTINCT advogado_oab) as num_advogados,
                COUNT(*) as case_count
            FROM processos
            WHERE tipo_parte IS NOT NULL AND advogado_oab IS NOT NULL
            GROUP BY tipo_parte
            ORDER BY case_count DESC
        """)
        return self.cursor.fetchall()
    
    def get_top_cases_per_role(self, limit=3):
        """Query: Top active cases per role"""
        self.cursor.execute("""
            SELECT 
                tipo_parte,
                nome_caso,
                status,
                data_inicio
            FROM processos
            WHERE tipo_parte IS NOT NULL AND status IN ('Aberto', 'Em andamento', 'ATIVO', 'PENDENTE')
            ORDER BY tipo_parte, data_inicio DESC
            LIMIT %s
        """, (limit,))
        return self.cursor.fetchall()
    
    def get_clients_per_role(self):
        """Query: Number of clients per role"""
        self.cursor.execute("""
            SELECT 
                tipo_parte,
                COUNT(DISTINCT id_cliente) as num_clients,
                COUNT(*) as total_cases
            FROM processos
            WHERE tipo_parte IS NOT NULL
            GROUP BY tipo_parte
            ORDER BY num_clients DESC
        """)
        return self.cursor.fetchall()
    
    def get_assignment_status(self):
        """Query: Percentage of cases with tipo_parte assigned"""
        self.cursor.execute("""
            SELECT 
                COUNT(CASE WHEN tipo_parte IS NOT NULL THEN 1 END) as assigned,
                COUNT(CASE WHEN tipo_parte IS NULL THEN 1 END) as unassigned,
                COUNT(*) as total,
                ROUND(100.0 * COUNT(CASE WHEN tipo_parte IS NOT NULL THEN 1 END) / COUNT(*), 2) as assignment_percentage
            FROM processos
        """)
        return self.cursor.fetchone()
    
    def get_cases_by_client_and_role(self, id_cliente):
        """Query: Cases for specific client grouped by role"""
        self.cursor.execute("""
            SELECT 
                tipo_parte,
                COUNT(*) as count,
                status
            FROM processos
            WHERE id_cliente = %s
            GROUP BY tipo_parte, status
            ORDER BY count DESC
        """, (id_cliente,))
        return self.cursor.fetchall()
    
    def print_analytics_report(self):
        """Print comprehensive analytics report"""
        print("\n" + "="*80)
        print("PHASE 5: TIPO_PARTE ANALYTICS DASHBOARD")
        print("="*80)
        
        # 1. Assignment Status
        print("\n📊 Assignment Status:")
        status = self.get_assignment_status()
        print(f"   Total processes: {status['total']}")
        print(f"   ✓ With tipo_parte: {status['assigned']} ({status['assignment_percentage']}%)")
        print(f"   ✗ Without tipo_parte: {status['unassigned']}")
        
        # 2. Distribution by Role
        print("\n📈 Distribution by Role:")
        distribution = self.get_distribution_by_role()
        for row in distribution:
            percentage = float(row['percentage'])
            bar = "█" * (int(percentage) // 5)  # Create simple bar chart
            print(f"   • {row['tipo_parte']:12} {bar:20} {row['count']:3} cases ({percentage:5.1f}%)")
        
        # 3. Status Breakdown per Role
        print("\n🔄 Status Distribution by Role:")
        status_by_role = self.get_status_by_role()
        current_role = None
        for row in status_by_role:
            if row['tipo_parte'] != current_role:
                current_role = row['tipo_parte']
                print(f"\n   {row['tipo_parte'].upper()}:")
            print(f"      • {row['status']}: {row['count']}")
        
        # 4. Advogados per Role
        print("\n👨‍⚖️  Advogados Assignment:")
        avogados_data = self.get_advogados_per_role()
        for row in avogados_data:
            avg = row['case_count'] / row['num_advogados'] if row['num_advogados'] > 0 else 0
            print(f"   • {row['tipo_parte']}: {row['num_advogados']} advogados handling {row['case_count']} cases (~{avg:.1f} per advogado)")
        
        # 5. Clients per Role
        print("\n👥 Clients by Role:")
        clients_data = self.get_clients_per_role()
        for row in clients_data:
            print(f"   • {row['tipo_parte']}: {row['num_clients']} clients with {row['total_cases']} cases")
        
        # 6. Active Cases
        print("\n📌 Active Cases (sample):")
        active_cases = self.get_top_cases_per_role(limit=5)
        current_role = None
        for row in active_cases:
            if row['tipo_parte'] != current_role:
                current_role = row['tipo_parte']
                print(f"\n   {row['tipo_parte'].upper()}:")
            case_name = row['nome_caso'][:50] + "..." if len(row['nome_caso']) > 50 else row['nome_caso']
            print(f"      • {case_name} ({row['status']})")

def main():
    analytics = TipoParteAnalytics()
    try:
        analytics.print_analytics_report()
        print("\n" + "="*80)
        print("✅ Analytics report complete!")
        print("="*80 + "\n")
    finally:
        analytics.close()

if __name__ == '__main__':
    main()
