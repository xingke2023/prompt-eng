"""
One-time migration: reads from MySQL insurancetools.customer_cases
and inserts into PostgreSQL seedance_script.insurance_cases and insurance_qa.
"""
import os
import json
import pymysql
import psycopg2
import psycopg2.extras

MYSQL = dict(host="127.0.0.1", port=3306, user="root", password="", db="insurancetools", charset="utf8mb4")
PG = dict(
    host=os.environ.get("DB_HOST", "localhost"),
    port=int(os.environ.get("DB_PORT", 5432)),
    dbname=os.environ.get("DB_NAME", "seedance_script"),
    user=os.environ.get("DB_USER", "fenjing_app"),
    password=os.environ.get("DB_PASSWORD", ""),
)

def run():
    mysql_conn = pymysql.connect(**MYSQL)
    pg_conn    = psycopg2.connect(**PG)
    pg_cur     = pg_conn.cursor()

    with mysql_conn.cursor(pymysql.cursors.DictCursor) as cur:
        # ── 港险案例 ──────────────────────────────────────────────
        cur.execute("""
            SELECT id, title, tags, customer_age, family_structure,
                   insurance_needs, case_description, content,
                   key_points, budget_suggestion, sort_order
            FROM customer_cases
            WHERE category = '港险案例' AND is_active = 1
            ORDER BY sort_order, id
        """)
        cases = cur.fetchall()
    print(f"Fetched {len(cases)} 港险案例 rows")

    # Clear existing to allow re-run
    pg_cur.execute("TRUNCATE insurance_cases RESTART IDENTITY")

    case_rows = []
    for r in cases:
        tags = r["tags"] if isinstance(r["tags"], list) else (json.loads(r["tags"]) if r["tags"] else [])
        kp   = r["key_points"] if isinstance(r["key_points"], list) else (json.loads(r["key_points"]) if r["key_points"] else [])
        is_featured = "热门案例" in tags
        case_rows.append((
            r["id"],
            r["title"],
            tags,
            r["customer_age"],
            r["family_structure"] or "",
            r["insurance_needs"] or "",
            r["case_description"] or "",
            r["content"] or "",
            json.dumps(kp, ensure_ascii=False),
            r["budget_suggestion"] or "",
            is_featured,
            r["sort_order"] or 0,
        ))

    psycopg2.extras.execute_values(pg_cur, """
        INSERT INTO insurance_cases
            (source_id, title, tags, customer_age, family_structure,
             insurance_needs, description, content, key_points,
             budget_suggestion, is_featured, sort_order)
        VALUES %s
    """, case_rows, template="(%s,%s,%s::text[],%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s)")
    print(f"Inserted {len(case_rows)} insurance_cases")

    # ── 港险问答 ──────────────────────────────────────────────────
    with mysql_conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("""
            SELECT id, title, tags, case_description, content, sort_order
            FROM customer_cases
            WHERE category = '港险问答' AND is_active = 1
            ORDER BY sort_order, id
        """)
        qas = cur.fetchall()
    print(f"Fetched {len(qas)} 港险问答 rows")

    pg_cur.execute("TRUNCATE insurance_qa RESTART IDENTITY")

    qa_rows = []
    for r in qas:
        tags = r["tags"] if isinstance(r["tags"], list) else (json.loads(r["tags"]) if r["tags"] else [])
        body = r["content"] or r["case_description"] or ""
        qa_rows.append((
            r["id"],
            r["title"],
            tags,
            body,
            r["sort_order"] or 0,
        ))

    psycopg2.extras.execute_values(pg_cur, """
        INSERT INTO insurance_qa (source_id, title, tags, content, sort_order)
        VALUES %s
    """, qa_rows, template="(%s,%s,%s::text[],%s,%s)")
    print(f"Inserted {len(qa_rows)} insurance_qa")

    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()
    mysql_conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    run()
