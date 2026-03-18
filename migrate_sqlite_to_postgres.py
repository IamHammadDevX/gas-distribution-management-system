import argparse
import os
import sqlite3
from typing import Iterable, Sequence

try:
    import psycopg
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "psycopg is required. Install dependencies from requirements.txt before running this script."
    ) from exc


TABLE_ORDER: list[str] = [
    "users",
    "clients",
    "gas_products",
    "sales",
    "sale_items",
    "receipts",
    "gate_passes",
    "client_initial_outstanding",
    "weekly_invoices",
    "weekly_payments",
    "employees",
    "vehicle_expenses",
    "activity_logs",
    "backup_logs",
    "cylinder_returns",
]


def _default_pg_dsn() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    host = os.environ.get("PGHOST")
    dbname = os.environ.get("PGDATABASE")
    user = os.environ.get("PGUSER")
    password = os.environ.get("PGPASSWORD", "")
    port = os.environ.get("PGPORT", "5432")
    sslmode = os.environ.get("PGSSLMODE", "prefer")

    if not (host and dbname and user):
        raise SystemExit(
            "Missing Postgres connection info. Provide --postgres or set DATABASE_URL, or set PGHOST/PGDATABASE/PGUSER."
        )

    parts = [
        f"host={host}",
        f"port={port}",
        f"dbname={dbname}",
        f"user={user}",
        f"sslmode={sslmode}",
    ]
    if password:
        parts.append(f"password={password}")
    return " ".join(parts)


def _sqlite_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cur.fetchall()]


def _sqlite_rows(conn: sqlite3.Connection, table: str, columns: Sequence[str]) -> list[tuple]:
    cols = ", ".join(columns)
    cur = conn.execute(f"SELECT {cols} FROM {table}")
    return list(cur.fetchall())


def _pg_table_exists(conn: psycopg.Connection, table: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass(%s)", (table,))
        return cur.fetchone()[0] is not None


def _chunked(rows: Sequence[tuple], chunk_size: int) -> Iterable[Sequence[tuple]]:
    for i in range(0, len(rows), chunk_size):
        yield rows[i : i + chunk_size]


def _copy_table(
    pg_conn: psycopg.Connection,
    table: str,
    columns: Sequence[str],
    rows: Sequence[tuple],
    chunk_size: int,
) -> int:
    if not rows:
        return 0

    collist = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    on_conflict = " ON CONFLICT (id) DO NOTHING" if "id" in columns else ""
    sql = f"INSERT INTO {table} ({collist}) VALUES ({placeholders}){on_conflict}"

    inserted = 0
    with pg_conn.cursor() as cur:
        for chunk in _chunked(rows, chunk_size):
            cur.executemany(sql, chunk)
            inserted += len(chunk)
    return inserted


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate Rajput Gas SQLite data into PostgreSQL.")
    parser.add_argument("--sqlite", default="rajput_gas.db", help="Path to SQLite .db file")
    parser.add_argument(
        "--postgres",
        default=None,
        help="Postgres DSN/URL (if omitted, uses DATABASE_URL/PG* env vars)",
    )
    parser.add_argument("--chunk-size", type=int, default=2000, help="Insert batch size")
    parser.add_argument(
        "--wipe",
        action="store_true",
        help="Dangerous: truncate target tables before import",
    )
    args = parser.parse_args()

    sqlite_conn = sqlite3.connect(args.sqlite)
    sqlite_conn.row_factory = sqlite3.Row

    pg_dsn = args.postgres or _default_pg_dsn()
    pg_conn = psycopg.connect(pg_dsn, autocommit=False)

    try:
        with pg_conn:
            with pg_conn.cursor() as cur:
                cur.execute("SET synchronous_commit TO on")

            for table in TABLE_ORDER:
                if not _pg_table_exists(pg_conn, table):
                    print(f"Skipping missing table in Postgres: {table}")
                    continue

                columns = _sqlite_columns(sqlite_conn, table)
                if not columns:
                    continue

                rows = _sqlite_rows(sqlite_conn, table, columns)

                if args.wipe:
                    with pg_conn.cursor() as cur:
                        cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")

                copied = _copy_table(pg_conn, table, columns, rows, args.chunk_size)
                print(f"{table}: {copied} rows copied")

            # Fix sequences for BIGSERIAL id columns (best-effort).
            with pg_conn.cursor() as cur:
                for table in TABLE_ORDER:
                    if not _pg_table_exists(pg_conn, table):
                        continue
                    cur.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table}")
                    max_id = int(cur.fetchone()[0] or 0)
                    cur.execute("SELECT pg_get_serial_sequence(%s, 'id')", (table,))
                    seq = cur.fetchone()[0]
                    if seq:
                        cur.execute("SELECT setval(%s, %s, true)", (seq, max_id))

        return 0
    finally:
        sqlite_conn.close()
        pg_conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

