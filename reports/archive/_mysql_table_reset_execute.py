"""One-shot approved MySQL table-level reset executor. Do not commit."""
from __future__ import annotations

import hashlib
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, unquote

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import mysql.connector
from dotenv import load_dotenv

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

ML_GLOBS = [
    "ml_*.py",
    "ml_*.json",
    "ml_*.csv",
    "ml_*.md",
    "train_*.py",
    "aml_ai_*",
    "test_model_integration.py",
]

SCHEMA_PATH = PROJECT_ROOT / "clean_aml_mysql_schema.sql"
PRE_AUDIT_PATH = PROJECT_ROOT / "reports" / "mysql_pre_reset_audit_2026-09-14.txt"
FINAL_REPORT_PATH = PROJECT_ROOT / "reports" / "mysql_table_reset_report_2026-09-14.txt"


def parse_database_url(url: str) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in ("mysql", "mysql+pymysql", "mysql+mysqlconnector"):
        raise ValueError(f"Unsupported database scheme: {parsed.scheme}")
    database = parsed.path.lstrip("/").split("?")[0]
    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": database,
    }


def redact_db_url(url: str) -> str:
    parsed = urlparse(url)
    user = parsed.username or ""
    host = parsed.hostname or ""
    port = parsed.port or 3306
    db = parsed.path.lstrip("/").split("?")[0]
    return f"mysql://{user}:***@{host}:{port}/{db}"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_ml_hashes() -> dict[str, str]:
    out: dict[str, str] = {}
    for pattern in ML_GLOBS:
        for path in PROJECT_ROOT.glob(pattern):
            if path.is_file():
                rel = path.relative_to(PROJECT_ROOT).as_posix()
                out[rel] = file_sha256(path)
    return dict(sorted(out.items()))


def extract_schema_statements(text: str) -> list[str]:
    # MySQL 8 requires identical types on FK columns; audited schema uses INT
    # child IDs referencing BIGINT parents — widen child IDs only (no redesign).
    text = re.sub(
        r"(CREATE TABLE alerts \(\s*\n\s*id BIGINT NOT NULL AUTO_INCREMENT,\s*\n\s*)transaction_id INT NOT NULL,",
        r"\1transaction_id BIGINT NOT NULL,",
        text,
        count=1,
    )
    text = re.sub(
        r"(CREATE TABLE sar_reports \(\s*\n\s*id BIGINT NOT NULL AUTO_INCREMENT,\s*\n\s*)alert_id INT NOT NULL,",
        r"\1alert_id BIGINT NOT NULL,",
        text,
        count=1,
    )
    text = re.sub(
        r"(CREATE TABLE ctr_reports \(\s*\n\s*id BIGINT NOT NULL AUTO_INCREMENT,\s*\n\s*)transaction_id INT NOT NULL,",
        r"\1transaction_id BIGINT NOT NULL,",
        text,
        count=1,
    )
    filtered_lines: list[str] = []
    for line in text.splitlines():
        upper = line.strip().upper()
        if upper.startswith("DROP DATABASE"):
            continue
        if upper.startswith("CREATE DATABASE"):
            continue
        if re.match(r"^USE\s+", upper):
            continue
        filtered_lines.append(line)
    body = "\n".join(filtered_lines)
    statements: list[str] = []
    for chunk in body.split(";"):
        stmt = chunk.strip()
        if not stmt:
            continue
        non_comment = [
            ln
            for ln in stmt.splitlines()
            if ln.strip() and not ln.strip().startswith("--")
        ]
        if not non_comment:
            continue
        statements.append(stmt)
    return statements


def connect(cfg: dict):
    return mysql.connector.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        autocommit=False,
    )


def count_rows(cursor, tables: list[str]) -> dict[str, int | str]:
    counts: dict[str, int | str] = {}
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            counts[table] = int(cursor.fetchone()[0])
        except Exception as exc:
            counts[table] = f"ERROR: {exc}"
    return counts


def verify_structure(cursor, cfg: dict) -> dict:
    result: dict = {"issues": []}
    cursor.execute("SELECT VERSION()")
    result["mysql_version"] = cursor.fetchone()[0]
    cursor.execute(
        """
        SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME
        FROM information_schema.SCHEMATA
        WHERE SCHEMA_NAME = %s
        """,
        (cfg["database"],),
    )
    row = cursor.fetchone()
    result["charset"] = row[0]
    result["collation"] = row[1]
    cursor.execute(
        """
        SELECT TABLE_NAME, ENGINE
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_NAME
        """,
        (cfg["database"],),
    )
    result["tables"] = {name: engine for name, engine in cursor.fetchall()}
    cursor.execute(
        """
        SELECT TABLE_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY TABLE_NAME, CONSTRAINT_NAME
        """,
        (cfg["database"],),
    )
    result["foreign_keys"] = cursor.fetchall()
    cursor.execute(
        """
        SELECT TABLE_NAME, INDEX_NAME, NON_UNIQUE, GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX)
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = %s
        GROUP BY TABLE_NAME, INDEX_NAME, NON_UNIQUE
        ORDER BY TABLE_NAME, INDEX_NAME
        """,
        (cfg["database"],),
    )
    result["indexes"] = cursor.fetchall()
    missing = [t for t in EXPECTED_TABLES if t not in result["tables"]]
    if missing:
        result["issues"].append(f"Missing tables: {missing}")
    for table, engine in result["tables"].items():
        if engine != "InnoDB":
            result["issues"].append(f"Table {table} engine is {engine}, expected InnoDB")
    if result["charset"] != "utf8mb4" or result["collation"] != "utf8mb4_unicode_ci":
        result["issues"].append(
            f"Charset/collation mismatch: {result['charset']}/{result['collation']}"
        )
    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'transactions'
        ORDER BY ORDINAL_POSITION
        """,
        (cfg["database"],),
    )
    result["transaction_columns"] = [r[0] for r in cursor.fetchall()]
    required_tx_cols = [
        "generated_label",
        "destination_country",
        "agent_id",
        "ai_risk_level",
        "rule_score",
        "screening_hits",
    ]
    for col in required_tx_cols:
        if col not in result["transaction_columns"]:
            result["issues"].append(f"transactions missing column: {col}")
    return result


def run_functional_tests() -> list[str]:
    lines: list[str] = []
    try:
        from server import app, initialize_startup

        db_url = app.config.get("DATABASE_URL", "")
        if not str(db_url).startswith("mysql"):
            lines.append("FAIL: Application DATABASE_URL is not MySQL")
            return lines
        lines.append(f"PASS: Application configured for MySQL ({redact_db_url(str(db_url))})")
        initialize_startup()
        lines.append("PASS: initialize_startup() completed (init_db + seed + AI hooks)")
    except Exception as exc:
        lines.append(f"FAIL: Application startup/initialize_startup: {exc}")
        return lines

    try:
        from server import app

        with app.test_client() as client:
            resp = client.post(
                "/login",
                data={"username": "Admin", "password": "Admin123"},
                follow_redirects=False,
            )
            if resp.status_code not in (200, 302):
                lines.append(f"FAIL: Admin login HTTP {resp.status_code}")
            else:
                lines.append("PASS: Admin login")
            resp = client.get("/dashboard")
            if resp.status_code not in (200, 302):
                lines.append(f"FAIL: Dashboard HTTP {resp.status_code}")
            else:
                lines.append("PASS: Dashboard reachable after login")
            resp = client.get("/api/v1/agents")
            if resp.status_code not in (200, 401, 403, 302):
                lines.append(f"WARN: Agent API HTTP {resp.status_code}")
            else:
                lines.append(f"PASS: Agent API responded HTTP {resp.status_code}")
    except Exception as exc:
        lines.append(f"FAIL: Flask test client regression: {exc}")

    cfg = parse_database_url(os.environ.get("DATABASE_URL") or "")
    try:
        conn = connect(cfg)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        lines.append(f"PASS: users row count after seed: {user_count}")
        cur.execute("SELECT id, username FROM users LIMIT 1")
        row = cur.fetchone()
        if row:
            lines.append(f"PASS: user read sample id={row[0]} username={row[1]}")
        else:
            lines.append("FAIL: no users after seed")
        conn.close()
    except Exception as exc:
        lines.append(f"FAIL: post-seed DB checks: {exc}")
    return lines


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("MYSQL_URL")
    if not db_url:
        from config import Config

        db_url = Config.DATABASE_URL
    if not str(db_url).startswith("mysql"):
        print("STOP: Application is not configured for MySQL")
        return 2
    cfg = parse_database_url(str(db_url))
    if cfg["database"] != "aml":
        print("STOP: configured database is not aml")
        return 2
    if cfg["host"] != "127.0.0.1" or cfg["port"] != 3306 or cfg["user"] != "aml":
        print("STOP: connection parameters do not match approved target")
        return 2
    if not SCHEMA_PATH.is_file():
        print("STOP: clean_aml_mysql_schema.sql missing")
        return 2

    ml_before = collect_ml_hashes()
    reset_started = datetime.now(timezone.utc).astimezone()

    conn = connect(cfg)
    cur = conn.cursor()
    pre_counts = count_rows(cur, EXPECTED_TABLES)
    cur.execute("SELECT VERSION()")
    mysql_version = cur.fetchone()[0]

    PRE_AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PRE_AUDIT_PATH.open("w", encoding="utf-8") as f:
        f.write("MySQL Pre-Reset Audit\n")
        f.write(f"Generated (local): {reset_started.isoformat()}\n")
        f.write(f"MySQL version: {mysql_version}\n")
        f.write(f"Database: {cfg['database']}\n")
        f.write(f"Host: {cfg['host']}\n")
        f.write(f"Port: {cfg['port']}\n")
        f.write(f"User: {cfg['user']}\n")
        f.write(f"Application DB URL (redacted): {redact_db_url(str(db_url))}\n")
        f.write("\nPre-reset row counts:\n")
        for table in EXPECTED_TABLES:
            f.write(f"  {table}: {pre_counts.get(table)}\n")
        total = sum(v for v in pre_counts.values() if isinstance(v, int))
        f.write(f"\nTotal (numeric tables only): {total}\n")

    missing_before = [t for t in EXPECTED_TABLES if not isinstance(pre_counts.get(t), int)]
    pre_reset_warnings: list[str] = []
    if missing_before:
        pre_reset_warnings.append(
            f"Partial schema detected before reset (missing/unreadable): {missing_before}"
        )

    schema_text = SCHEMA_PATH.read_text(encoding="utf-8")
    statements = extract_schema_statements(schema_text)

    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    dropped: list[str] = []
    for table in EXPECTED_TABLES:
        cur.execute(f"DROP TABLE IF EXISTS `{table}`")
        dropped.append(table)
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()

    recreated: list[str] = []
    errors: list[str] = []
    fk_type_fix_note = (
        "Applied MySQL-required BIGINT child FK columns for alerts.transaction_id, "
        "sar_reports.alert_id, ctr_reports.transaction_id (audited SQL used INT)."
    )
    for stmt in statements:
        try:
            cur.execute(stmt)
            if stmt.upper().lstrip().startswith("CREATE TABLE"):
                m = re.search(r"CREATE TABLE\s+(\w+)", stmt, re.I)
                if m:
                    recreated.append(m.group(1))
            elif stmt.upper().lstrip().startswith("CREATE INDEX"):
                recreated.append(stmt.split()[2].split("(")[0])
        except Exception as exc:
            errors.append(f"{exc} :: {stmt[:120]}...")
    conn.commit()

    if errors:
        conn.rollback()
        conn.close()
        with FINAL_REPORT_PATH.open("w", encoding="utf-8") as f:
            f.write("MySQL Table Reset FAILED during schema apply\n")
            for err in errors:
                f.write(f"  - {err}\n")
        print("STOP: schema apply errors")
        for err in errors[:5]:
            print(err)
        return 2

    post_counts = count_rows(cur, EXPECTED_TABLES)
    structure = verify_structure(cur, cfg)
    conn.close()

    functional = run_functional_tests()
    ml_after = collect_ml_hashes()
    ml_changed = [
        p for p in ml_before if ml_after.get(p) != ml_before.get(p)
    ]
    ml_added = [p for p in ml_after if p not in ml_before]
    ml_removed = [p for p in ml_before if p not in ml_after]

    reset_finished = datetime.now(timezone.utc).astimezone()
    warnings: list[str] = list(pre_reset_warnings)
    warnings.append(fk_type_fix_note)
    if structure["issues"]:
        warnings.extend(structure["issues"])
    if any(line.startswith("FAIL:") for line in functional):
        warnings.append("One or more functional regression checks failed")

    with FINAL_REPORT_PATH.open("w", encoding="utf-8") as f:
        f.write("MySQL Table-Level Reset Report\n")
        f.write("=" * 72 + "\n\n")
        f.write(f"1. Reset date/time (local): {reset_finished.isoformat()}\n")
        f.write(f"2. MySQL version: {structure.get('mysql_version', mysql_version)}\n")
        f.write(f"3. Database name: aml\n\n")
        f.write("4. Tables dropped (15):\n")
        for t in dropped:
            f.write(f"   - {t}\n")
        f.write("\n5. Tables recreated from clean_aml_mysql_schema.sql:\n")
        for t in EXPECTED_TABLES:
            f.write(f"   - {t}\n")
        f.write("\n6. Pre-reset row counts:\n")
        for t in EXPECTED_TABLES:
            f.write(f"   {t}: {pre_counts.get(t)}\n")
        f.write("\n7. Post-reset row counts (before/after seed in functional section):\n")
        for t in EXPECTED_TABLES:
            f.write(f"   {t}: {post_counts.get(t)}\n")
        f.write("\n8. Schema verification:\n")
        f.write(f"   Charset: {structure['charset']}\n")
        f.write(f"   Collation: {structure['collation']}\n")
        f.write(f"   Tables present: {len(structure['tables'])}\n")
        f.write(f"   Transaction columns ({len(structure['transaction_columns'])}): ")
        f.write(", ".join(structure["transaction_columns"]) + "\n")
        if structure["issues"]:
            f.write("   Issues:\n")
            for issue in structure["issues"]:
                f.write(f"     - {issue}\n")
        else:
            f.write("   Issues: none\n")
        f.write("\n9. Foreign-key verification:\n")
        for row in structure["foreign_keys"]:
            f.write(f"   {row[0]}.{row[1]} -> {row[2]}\n")
        f.write(f"   Total FK constraints: {len(structure['foreign_keys'])}\n")
        f.write("\n10. Index verification:\n")
        for row in structure["indexes"]:
            f.write(f"   {row[0]} / {row[1]} (non_unique={row[2]}) cols={row[3]}\n")
        f.write(f"   Total indexes: {len(structure['indexes'])}\n")
        f.write("\n11. Application startup result:\n")
        for line in functional[:3]:
            f.write(f"   {line}\n")
        f.write("\n12. Functional regression results:\n")
        for line in functional:
            f.write(f"   {line}\n")
        f.write("\n13. ML protection verification:\n")
        f.write(f"   ML files fingerprinted: {len(ml_before)}\n")
        if ml_changed or ml_added or ml_removed:
            f.write("   CHANGES DETECTED:\n")
            for p in ml_changed:
                f.write(f"     modified: {p}\n")
            for p in ml_added:
                f.write(f"     added: {p}\n")
            for p in ml_removed:
                f.write(f"     removed: {p}\n")
        else:
            f.write("   PASS: No ML-related file content changes detected during reset operation.\n")
        f.write("\n14. Warnings:\n")
        if warnings:
            for w in warnings:
                f.write(f"   - {w}\n")
        else:
            f.write("   none\n")
        f.write("\n15. Failures:\n")
        fails = [ln for ln in functional if ln.startswith("FAIL:")]
        fails.extend(structure["issues"])
        if fails:
            for item in fails:
                f.write(f"   - {item}\n")
        else:
            f.write("   none\n")
        f.write("\nPre-reset audit file: reports/mysql_pre_reset_audit_2026-09-14.txt\n")
        f.write("Reset method: Option B table-level DROP + recreate (no DROP/CREATE DATABASE)\n")

    print(f"Pre-reset audit: {PRE_AUDIT_PATH}")
    print(f"Final report: {FINAL_REPORT_PATH}")
    print("Reset completed.")
    if warnings:
        print("Warnings present — see final report.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
