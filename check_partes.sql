-- Verificar partes adversas salvas
SELECT id, nome_completo, tipo_parte, tenant_id, created_at 
FROM partes_adversas 
WHERE id_processo = 'caso_11b044bc'
ORDER BY id;
