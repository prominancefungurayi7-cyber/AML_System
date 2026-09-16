"""One-off approved table-level MySQL reset (Option B). Do not print secrets."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
import os

load_dotenv(PROJECT_ROOT / ".env")

from database import connect_db, is_mysql_database_url

EXPECTED_TABLES = [
    "users",
    "transactions",
    "agents",
    "alerts",
    "sar_reports",
    "ctr_reports",
    "customer_baselines",
    "conversations",
    "messages",
    "unread_messages",
    "user_presence",
    "behavioral_profiles",
    "system_activity_log",
    "activity_log",
    "watchlist",
]

SCHEMA_PATH = PROJECT_ROOT / "clean_aml_mysql_schema.sql"
REPORTS_DIR = PROJECT_ROOT / "reports"
PRE_AUDIT_PATH = REPORTS_DIR / "mysql_pre_reset_audit_2026-09-14.txt"
RESULT_PATH = REPORTS_DIR / "_table_reset_result.json"


def database_url_safe_info(url: str) -> dict:
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "database": (parsed.path or "").lstrip("/"),
        "user": unquote(parsed.username or ""),
        "is_mysql": is_mysql_database_url(url),
    }


def parse_schema_ddl(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        upper = stripped.upper()
        if upper.startswith("DROP DATABASE"):
            continue
        if upper.startswith("CREATE DATABASE"):
            continue
        if upper.startswith("USE "):
            continue
        lines.append(line)
    body = "\n".join(lines)
    statements = []
    for part in body.split(";"):
        stmt = part.strip()
        if stmt:
            statements.append(stmt + ";")
    return statements


def fetch_row_counts(conn) -> dict[str, int]:
    counts = {}
    for table in EXPECTED_TABLES:
        cur = conn.execute(f"SELECT COUNT(*) AS c FROM `{table}`")
        row = cur.fetchone()
        if isinstance(row, dict):
            counts[table] = int(row["c"])
        else:
            counts[table] = int(row[0])
    return counts


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("MYSQL_URL") or ""
    info = database_url_safe_info(db_url)

    if not info["is_mysql"]:
        print("STOP: Application is not configured for MySQL")
        return 1
    if info["database"] != "aml":
        print("STOP: Configured database is not aml")
        return 1
    if info["host"] not in ("127.0.0.1", "localhost"):
        print("STOP: Unexpected MySQL host")
        return 1
    if info["port"] != 3306:
        print("STOP: Unexpected MySQL port")
        return 1
    if info["user"] != "aml":
        print("STOP: Unexpected MySQL user")
        return 1

    if not SCHEMA_PATH.is_file():
        print("STOP: clean_aml_mysql_schema.sql missing")
        return 1

    schema_text = SCHEMA_PATH.read_text(encoding="utf-8")
    ddl_statements = parse_schema_ddl(schema_text)
    if not ddl_statements:
        print("STOP: Could not parse schema DDL safely")
        return 1

    conn = connect_db(db_url)
    cur = conn.connection.cursor(dictionary=True)

    cur.execute("SELECT VERSION() AS v")
    mysql_version = cur.fetchone()["v"]

    cur.execute(
        "SELECT DEFAULT_CHARACTER_SET_NAME AS cs, DEFAULT_COLLATION_NAME AS coll "
        "FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s",
        (info["database"],),
    )
    db_meta = cur.fetchone()

    cur.execute(
        "SELECT TABLE_NAME FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'",
        (info["database"],),
    )
    existing_tables = sorted(r["TABLE_NAME"] for r in cur.fetchall())
    missing = [t for t in EXPECTED_TABLES if t not in existing_tables]
    if missing:
        print("STOP: Missing expected tables:", ", ".join(missing))
        return 1

    pre_counts = fetch_row_counts(conn)
    pre_total = sum(pre_counts.values())

    pre_lines = [
        "MySQL Pre-Reset Audit",
        f"Generated: {datetime.now(timezone.utc).astimezone().isoformat()}",
        "",
        "Connection (safe fields only):",
        f"  Host: {info['host']}",
        f"  Port: {info['port']}",
        f"  Database: {info['database']}",
        f"  User: {info['user']}",
        f"  MySQL Version: {mysql_version}",
        "",
        "Pre-reset row counts:",
    ]
    for table in EXPECTED_TABLES:
        pre_lines.append(f"  {table}: {pre_counts[table]}")
    pre_lines.append(f"  TOTAL: {pre_total}")
    PRE_AUDIT_PATH.write_text("\n".join(pre_lines) + "\n", encoding="utf-8")

    # Table-level reset
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    dropped = []
    for table in existing_tables:
        cur.execute(f"DROP TABLE IF EXISTS `{table}`")
        dropped.append(table)
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")

    for stmt in ddl_statements:
        cur.execute(stmt)

    conn.commit()

    cur.execute(
        "SELECT TABLE_NAME FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'",
        (info["database"],),
    )
    post_tables = sorted(r["TABLE_NAME"] for r in cur.fetchall())
    post_missing = [t for t in EXPECTED_TABLES if t not in post_tables]
    if post_missing:
        print("STOP: Tables missing after recreate:", ", ".join(post_missing))
        return 1

    post_counts = fetch_row_counts(conn)

    cur.execute(
        "SELECT TABLE_NAME, ENGINE FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'",
        (info["database"],),
    )
    engines = {r["TABLE_NAME"]: r["ENGINE"] for r in cur.fetchall()}

    cur.execute(
        "SELECT TABLE_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME "
        "FROM information_schema.KEY_COLUMN_USAGE "
        "WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL "
        "ORDER BY TABLE_NAME, CONSTRAINT_NAME",
        (info["database"],),
    )
    foreign_keys = cur.fetchall()

    cur.execute(
        "SELECT TABLE_NAME, INDEX_NAME, NON_UNIQUE, GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS cols "
        "FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = %s "
        "GROUP BY TABLE_NAME, INDEX_NAME, NON_UNIQUE ORDER BY TABLE_NAME, INDEX_NAME",
        (info["database"],),
    )
    indexes = cur.fetchall()

    cur.execute(
        "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'transactions' ORDER BY ORDINAL_POSITION",
        (info["database"],),
    )
    transaction_columns = [r["COLUMN_NAME"] for r in cur.fetchall()]

    result = {
        "reset_time": datetime.now(timezone.utc).astimezone().isoformat(),
        "mysql_version": mysql_version,
        "database": info["database"],
        "charset": db_meta["cs"] if db_meta else None,
        "collation": db_meta["coll"] if db_meta else None,
        "tables_dropped": dropped,
        "tables_recreated": post_tables,
        "pre_counts": pre_counts,
        "post_counts": post_counts,
        "engines": engines,
        "foreign_keys": foreign_keys,
        "indexes": indexes,
        "transaction_columns": transaction_columns,
        "ddl_statement_count": len(ddl_statements),
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print("TABLE_RESET_OK")
    print(f"pre_total={pre_total}")
    print(f"post_total={sum(post_counts.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
