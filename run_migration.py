"""
run_migration.py — Execute database migration to fix schema issues

This script runs the database migration to add missing columns that are
required for transaction generation.
"""

import os
import sys

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import app, get_db, is_postgres_database_url, is_mysql_database_url
from database import connect_db
from messaging import create_messaging_tables_sql


def _migrate_mysql(conn):
    """Widen older MySQL VARCHAR columns that store AML evidence JSON/text."""
    column_migrations = {
        "users": [
            ("kyc_status", "VARCHAR(255) DEFAULT 'pending'"),
            ("pep_flag", "INTEGER DEFAULT 0"),
            ("risk_rating", "VARCHAR(255) DEFAULT 'standard'"),
            ("wealth_segment", "VARCHAR(255) DEFAULT 'average'"),
        ],
        "transactions": [
            ("currency", "VARCHAR(255) DEFAULT 'USD'"),
            ("channel", "VARCHAR(255) DEFAULT 'online'"),
            ("rule_score", "DOUBLE DEFAULT 0"),
            ("rule_level", "VARCHAR(255) DEFAULT 'normal'"),
            ("rule_reason", "LONGTEXT"),
            ("ai_risk_level", "VARCHAR(255)"),
            ("ai_confidence", "DOUBLE DEFAULT 0"),
            ("ai_reason", "LONGTEXT"),
            ("rules_triggered", "LONGTEXT DEFAULT '[]'"),
            ("ctr_required", "INTEGER DEFAULT 0"),
            ("sar_required", "INTEGER DEFAULT 0"),
            ("destination_country", "VARCHAR(255) DEFAULT 'ZW'"),
            ("screening_hits", "LONGTEXT"),
            ("reviewed_by", "VARCHAR(255)"),
            ("reviewed_at", "DATETIME"),
            ("generated_label", "VARCHAR(255)"),
            ("status", "VARCHAR(255) DEFAULT 'Completed'"),
            ("agent_id", "INTEGER"),
        ],
        "alerts": [
            ("rules_triggered", "LONGTEXT DEFAULT '[]'"),
            ("status", "VARCHAR(255) DEFAULT 'open'"),
            ("assigned_to", "VARCHAR(255)"),
            ("case_notes", "LONGTEXT"),
            ("resolved_at", "DATETIME"),
            ("resolved_by", "VARCHAR(255)"),
        ],
        "behavioral_profiles": [
            ("account_number", "VARCHAR(255) PRIMARY KEY"),
            ("profile_data", "LONGTEXT"),
            ("last_updated", "DATETIME"),
            ("total_transactions", "INTEGER DEFAULT 0"),
        ],
    }

    for table, columns in column_migrations.items():
        for column_name, column_def in columns:
            try:
                # Check if column exists
                check_sql = f"""
                    SELECT COUNT(*) as count
                    FROM information_schema.columns
                    WHERE table_schema = DATABASE()
                    AND table_name = '{table}'
                    AND column_name = '{column_name}'
                """
                result = conn.execute(check_sql).fetchone()
                if result['count'] == 0:
                    # Column doesn't exist, add it
                    alter_sql = f"ALTER TABLE {table} ADD COLUMN {column_name} {column_def}"
                    print(f"Adding column {column_name} to {table}...")
                    conn.execute(alter_sql)
                else:
                    print(f"Column {column_name} already exists in {table}")
            except Exception as e:
                print(f"Error adding column {column_name} to {table}: {e}")

    # Create messaging tables if they don't exist
    messaging_sql = create_messaging_tables_sql(app.config["DATABASE"])
    for statement in messaging_sql.split(";"):
        statement = statement.strip()
        if statement:
            try:
                conn.execute(statement)
            except Exception as e:
                print(f"Error creating messaging table: {e}")


def _migrate_sqlite(conn):
    """Add columns that may not exist in older DB files."""
    migrations = {
        "users": ["kyc_status TEXT DEFAULT 'pending'", "pep_flag INTEGER DEFAULT 0", "risk_rating TEXT DEFAULT 'standard'", "wealth_segment TEXT DEFAULT 'average'"],
        "transactions": ["currency TEXT DEFAULT 'USD'", "channel TEXT DEFAULT 'online'",
                         "rule_score REAL DEFAULT 0", "rule_level TEXT DEFAULT 'normal'",
                         "rule_reason TEXT", "ai_risk_level TEXT", "ai_confidence REAL DEFAULT 0",
                         "ai_reason TEXT",
                         "rules_triggered TEXT DEFAULT '[]'", "ctr_required INTEGER DEFAULT 0",
                         "sar_required INTEGER DEFAULT 0", "destination_country TEXT DEFAULT 'ZW'",
                         "screening_hits TEXT", "reviewed_by TEXT", "reviewed_at TEXT",
                         "generated_label TEXT", "status TEXT DEFAULT 'Completed'", "agent_id INTEGER"],
        "alerts": ["rules_triggered TEXT DEFAULT '[]'", "status TEXT DEFAULT 'open'",
                   "assigned_to TEXT", "case_notes TEXT", "resolved_at TEXT", "resolved_by TEXT"],
        "behavioral_profiles": ["account_number TEXT PRIMARY KEY", "profile_data TEXT", "last_updated TEXT", "total_transactions INTEGER DEFAULT 0"],
    }

    for table, cols in migrations.items():
        existing = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        for col_def in cols:
            col_name = col_def.split()[0]
            if col_name not in existing:
                print(f"Adding column {col_name} to {table}...")
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
            else:
                print(f"Column {col_name} already exists in {table}")

    # Create messaging tables if they don't exist
    messaging_sql = create_messaging_tables_sql(app.config["DATABASE"])
    for statement in messaging_sql.split(";"):
        statement = statement.strip()
        if statement:
            conn.execute(statement)


def main():
    """Run the database migration."""
    print("Starting database migration...")

    with app.app_context():
        conn = get_db()

        try:
            # Execute schema SQL
            print("Executing schema SQL...")
            from database import get_schema_sql
            conn.executescript(get_schema_sql(app.config["DATABASE"]))

            # Execute messaging tables SQL
            print("Executing messaging tables SQL...")
            conn.executescript(create_messaging_tables_sql(app.config["DATABASE"]))

            # Run appropriate migration
            if is_postgres_database_url(app.config["DATABASE"]):
                print("Running PostgreSQL migration...")
                from server import _migrate_postgres
                _migrate_postgres(conn)
            elif is_mysql_database_url(app.config["DATABASE"]):
                print("Running MySQL migration...")
                _migrate_mysql(conn)
            else:
                print("Running SQLite migration...")
                _migrate_sqlite(conn)

            conn.commit()
            print("Database migration completed successfully!")
            print("You can now try generating transactions again.")

        except Exception as e:
            conn.rollback()
            print(f"Database migration failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
