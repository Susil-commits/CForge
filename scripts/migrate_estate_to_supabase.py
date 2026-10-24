"""Migrate ContextForge Estate Tables to Supabase Cloud PostgreSQL."""

import os
import sys
from pathlib import Path
import duckdb
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

def migrate():
    supabase_url = os.getenv("SUPABASE_DB_URL")
    if not supabase_url:
        print("ERROR: SUPABASE_DB_URL not set in .env")
        sys.exit(1)

    print("Connecting to Supabase PostgreSQL...")
    pg_conn = psycopg2.connect(supabase_url)
    pg_cur = pg_conn.cursor()

    estate_db = Path("data/estate.duckdb")
    if not estate_db.exists():
        print("ERROR: data/estate.duckdb not found.")
        sys.exit(1)

    print("Connecting to local DuckDB estate...")
    duck_conn = duckdb.connect(str(estate_db), read_only=True)
    tables = [r[0] for r in duck_conn.execute("SHOW TABLES").fetchall()]
    print(f"Found {len(tables)} tables to migrate.")

    type_map = {
        "VARCHAR": "TEXT",
        "BIGINT": "BIGINT",
        "INTEGER": "INTEGER",
        "INT": "INTEGER",
        "DOUBLE": "DOUBLE PRECISION",
        "FLOAT": "REAL",
        "BOOLEAN": "BOOLEAN",
        "TIMESTAMP": "TIMESTAMP",
        "DATE": "DATE",
    }

    migrated_count = 0

    for table in tables:
        # Get schema
        schema = duck_conn.execute(f"DESCRIBE {table}").fetchall()
        col_defs = []
        col_names = []
        for col_name, col_type, null_ok, *_ in schema:
            col_names.append(f'"{col_name}"')
            t_clean = col_type.split("(")[0].upper()
            pg_type = type_map.get(t_clean, "TEXT")
            col_defs.append(f'"{col_name}" {pg_type}')

        # Create Table in PostgreSQL
        ddl = f'CREATE TABLE IF NOT EXISTS public."{table}" (\n  ' + ",\n  ".join(col_defs) + "\n);"
        pg_cur.execute(ddl)

        # Check existing row count in Postgres
        pg_cur.execute(f'SELECT COUNT(*) FROM public."{table}";')
        existing_rows = pg_cur.fetchone()[0]

        if existing_rows == 0:
            # Transfer up to 500 rows per table for rapid demo sync
            rows = duck_conn.execute(f"SELECT * FROM {table} LIMIT 500").fetchall()
            if rows:
                cols_str = ", ".join(col_names)
                insert_sql = f'INSERT INTO public."{table}" ({cols_str}) VALUES %s;'
                # Convert tuples with python datatypes
                clean_rows = []
                for r in rows:
                    clean_rows.append(tuple(None if v is None else v for v in r))
                execute_values(pg_cur, insert_sql, clean_rows, page_size=250)
                pg_conn.commit()
                print(f"  [OK] {table}: Created schema & migrated {len(rows)} sample rows.")
            else:
                pg_conn.commit()
                print(f"  [OK] {table}: Created empty schema.")
        else:
            print(f"  [OK] {table}: Table exists with {existing_rows} rows (skipped insert).")

        migrated_count += 1

    pg_cur.close()
    pg_conn.close()
    duck_conn.close()
    print(f"\nSUCCESS: Migrated {migrated_count} tables to Supabase Cloud PostgreSQL!")

if __name__ == "__main__":
    migrate()
