"""Nonsecret restart/concurrency fixture only. NOT a custody backend.

Deleting or rolling back this developer-owned database defeats the guard.
No generator, RNG, evaluator, secret or dataset interface is provided.
"""
import sqlite3
import sys


def operate(path, operation):
    with sqlite3.connect(path, timeout=20) as db:
        db.execute('PRAGMA synchronous=FULL')
        db.execute('BEGIN IMMEDIATE')
        db.execute('CREATE TABLE IF NOT EXISTS fixture (id TEXT PRIMARY KEY, state TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS audit (operation TEXT, outcome TEXT)')
        if operation == 'authorize':
            result = db.execute("INSERT OR IGNORE INTO fixture VALUES ('NONSECRET_TEST_ONLY','AUTHORIZED')").rowcount
        elif operation == 'consume':
            result = db.execute("UPDATE fixture SET state='CONSUMED' WHERE id='NONSECRET_TEST_ONLY' AND state='AUTHORIZED'").rowcount
        else:
            raise ValueError('Unsupported fixture operation')
        outcome = 'ALLOWED' if result == 1 else 'DENIED'
        db.execute('INSERT INTO audit VALUES (?,?)', (operation, outcome))
        return outcome


if __name__ == '__main__':
    print(operate(sys.argv[1], sys.argv[2]))
