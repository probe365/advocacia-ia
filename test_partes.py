#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste rápido de partes adversas"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from cadastro_manager import CadastroManager

# Testar com tenant_id=public
mgr = CadastroManager(tenant_id='public')
partes = mgr.get_partes_adversas_by_processo('caso_11b044bc')

print(f"\n✅ Partes encontradas: {len(partes) if partes else 0}")
print(f"   tenant_id usado: {mgr.tenant_id}")
print(f"   multi_tenant: {mgr.multi_tenant}\n")

if partes:
    for p in partes:
        print(f"   ID: {p.get('id')} - {p.get('nome_completo')} ({p.get('tipo_parte')})")
        print(f"      tenant_id: {p.get('tenant_id')}")
        print()
else:
    print("   ❌ Nenhuma parte encontrada!\n")
    
    # Verificar quantas existem no total (sem filtro tenant)
    import psycopg2
    conn = psycopg2.connect(
        host='localhost',
        dbname='advocacia_ia',
        user='postgres',
        password='postgres'
    )
    cur = conn.cursor()
    cur.execute("SELECT id, nome_completo, tenant_id FROM partes_adversas WHERE id_processo = %s", ('caso_11b044bc',))
    todas = cur.fetchall()
    conn.close()
    
    print(f"   📊 Total no banco (sem filtro): {len(todas)}")
    for t in todas:
        print(f"      ID {t[0]}: {t[1]} (tenant_id={t[2]})")
