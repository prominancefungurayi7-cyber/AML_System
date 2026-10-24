"""Offline tests cannot connect to deployment databases or send email."""
import os

import pytest

collect_ignore_glob = ['archive/*']


def pytest_configure(config):
    os.environ.update(DATABASE_URL="sqlite:///:memory:", MYSQL_URL="sqlite:///:memory:",
                      AML_PRIMARY_MODEL="V4", SOCKETIO_ALLOWED_ORIGINS="http://127.0.0.1:5000")
    os.environ["REDIS_URL"] = ""
    os.environ["KAFKA_BOOTSTRAP_SERVERS"] = ""
    import database
    original = database.connect_db

    def offline_connection(url):
        if database.is_mysql_database_url(url) or database.is_postgres_database_url(url):
            raise RuntimeError("Offline tests cannot access a deployment database")
        return original(url)

    database.connect_db = offline_connection
    import mysql.connector
    def no_mysql(*args, **kwargs):
        raise RuntimeError('Offline tests cannot open a MySQL connection')
    mysql.connector.connect = no_mysql


@pytest.fixture(autouse=True)
def block_external_effects(monkeypatch):
    import smtplib
    def blocked(*args, **kwargs):
        raise AssertionError("Real SMTP is forbidden in offline tests")
    monkeypatch.setattr(smtplib, "SMTP", blocked)
    monkeypatch.setattr(smtplib, "SMTP_SSL", blocked)


@pytest.fixture
def aml_app(tmp_path, monkeypatch):
    """Load routes without startup, seeding, monitors, Redis or live SQL."""
    import ast
    from pathlib import Path
    import sys
    import types
    root = Path(__file__).resolve().parents[1]
    tree = ast.parse((root / "server.py").read_text(encoding="utf-8"))
    tree.body = [n for n in tree.body if not (
        isinstance(n, ast.If) and isinstance(n.test, ast.Compare)
        and isinstance(n.test.left, ast.Name) and n.test.left.id == "__name__"
    ) and not (
        isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
        and isinstance(n.value.func, ast.Name) and n.value.func.id == "load_dotenv"
    )]
    module = types.ModuleType("offline_application")
    module.__file__ = str(root / "server.py")
    monkeypatch.setitem(sys.modules, module.__name__, module)
    exec(compile(tree, module.__file__, "exec"), module.__dict__)
    url = "sqlite:///" + str(tmp_path / "application.sqlite")
    module.app.config.update(TESTING=True, SECRET_KEY="offline-test-secret", DATABASE=url,
                             DATABASE_URL=url, MONITOR_STOP=True,
                             PROFILE_PHOTO_ROOT=str(tmp_path / 'profile-photos'),
                             MESSAGE_ATTACHMENT_ROOT=str(tmp_path / 'message-attachments'))
    module.init_db()
    # Mirror the existing local MySQL reporting tables, which predate the
    # legacy schema factory. This DDL affects this temporary SQLite file only.
    db = module.connect_db()
    db.executescript('''
        DROP TABLE sar_reports;
        CREATE TABLE sar_reports (id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id INTEGER NOT NULL, account_number TEXT NOT NULL,
            filed_by TEXT NOT NULL, narrative TEXT, status TEXT DEFAULT 'draft',
            filed_at TEXT, reference_number TEXT, created_at TEXT NOT NULL);
        DROP TABLE ctr_reports;
        CREATE TABLE ctr_reports (id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL, account_number TEXT NOT NULL,
            amount REAL NOT NULL, generated_by TEXT NOT NULL,
            status TEXT DEFAULT 'pending', filed_at TEXT, created_at TEXT NOT NULL);
    ''')
    db.close()
    module.seed_demo_data()
    yield module
