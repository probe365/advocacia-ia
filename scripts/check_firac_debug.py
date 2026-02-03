import os
import psycopg2
from psycopg2.extras import RealDictCursor

params = {
    "dbname": os.getenv("DB_NAME", "advocacia_ia"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
}

pid = 26
case_id = "caso_ce4b2611"


def q(sql, args=()):
    with psycopg2.connect(**params) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, args)
            return cur.fetchall()


print("petition:", q("SELECT id, tenant_id, process_id, petition_type, content->>'fatos' AS fatos FROM petitions WHERE id=%s", (pid,)))
print("firac by caso_:", q("SELECT tenant_id, process_id, source, length(coalesce(facts,'')) AS facts_len, length(coalesce(rules,'')) AS rules_len FROM process_firac WHERE process_id=%s", (case_id,)))
print("firac by raw:", q("SELECT tenant_id, process_id, source, length(coalesce(facts,'')) AS facts_len, length(coalesce(rules,'')) AS rules_len FROM process_firac WHERE process_id=%s", (case_id.replace('caso_',''),)))
print("firac like:", q("SELECT process_id, count(*) FROM process_firac WHERE process_id LIKE %s GROUP BY process_id", ('%ce4b2611%',)))
