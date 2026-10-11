"""Administrator-only creation of the separately named, empty recovery schema.

No code in this module executes SQL at import time. CLI requires --apply.
"""
import argparse
import json
import os
import re

from ml_v4.stage4sg.recovery_guard import RECOVERY, REQUIRED, USER, UUID, grant_check

ACCOUNT_HOST = '127.0.0.1'
GRANT_SQL = ('GRANT ' + ', '.join(sorted(REQUIRED)) +
             f" ON `{RECOVERY}`.* TO '{USER}'@'{ACCOUNT_HOST}'")
CREATE_DATABASE_SQL = (f'CREATE DATABASE `{RECOVERY}` CHARACTER SET utf8mb4 '
                       'COLLATE utf8mb4_unicode_ci')
CREATE_USER_SQL = f"CREATE USER '{USER}'@'{ACCOUNT_HOST}' IDENTIFIED BY %s"


def provision(connection, recovery_password):
    """Fail before writes on identity/preexisting target; never retry partial DDL."""
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute('SELECT @@server_uuid AS uuid, CURRENT_USER() AS principal')
        identity = cursor.fetchone()
        if identity['uuid'] != UUID or not identity['principal']:
            raise ValueError('Administrator server identity mismatch')
        cursor.execute('SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s',
                       (RECOVERY,))
        if cursor.fetchone() is not None:
            raise ValueError('Recovery schema already exists; no changes made')
        cursor.execute('SELECT User,Host FROM mysql.user WHERE User=%s', (USER,))
        if cursor.fetchone() is not None:
            raise ValueError('Recovery account name already exists; no changes made')
        if not recovery_password or len(recovery_password) < 20:
            raise ValueError('Recovery password is missing or too short')

        # MySQL account/schema DDL implicitly commits. A later failure leaves a
        # partial target for administrator review, never an automatic retry.
        cursor.execute(CREATE_DATABASE_SQL)
        cursor.execute(CREATE_USER_SQL, (recovery_password,))
        cursor.execute(GRANT_SQL)

        cursor.execute(f"SHOW GRANTS FOR '{USER}'@'{ACCOUNT_HOST}'")
        grants = [next(iter(row.values())) for row in cursor.fetchall()]
        grant_check(grants, exact=True)
        cursor.execute('SELECT @@server_uuid AS uuid')
        if cursor.fetchone()['uuid'] != UUID:
            raise ValueError('Server UUID changed during provisioning')
        cursor.execute(f'SHOW FULL TABLES FROM `{RECOVERY}`')
        if cursor.fetchall():
            raise ValueError('New recovery database is not empty')
        return {'status': 'PROVISIONED_EMPTY_RECOVERY', 'database': RECOVERY,
                'account': USER + '@' + ACCOUNT_HOST, 'server_uuid': UUID,
                'privileges': sorted(REQUIRED), 'table_count': 0}
    finally:
        cursor.close()


def run():
    if os.environ.get('V4_STAGE4SL_EXPECTED_SERVER_UUID') != UUID:
        raise ValueError('Expected server UUID not pinned')
    admin_user = os.environ.get('V4_STAGE4SL_ADMIN_USER', '')
    if not re.fullmatch(r'[A-Za-z0-9_]{1,32}', admin_user) or admin_user == USER:
        raise ValueError('Administrator user invalid')
    admin_password = os.environ.pop('V4_STAGE4SL_ADMIN_PASSWORD', '')
    recovery_password = os.environ.pop('V4_STAGE4SL_RECOVERY_PASSWORD', '')
    if not admin_password or len(recovery_password) < 20:
        raise ValueError('Required password unavailable')
    import mysql.connector
    connection = mysql.connector.connect(host='127.0.0.1', port=3306,
                                          user=admin_user, password=admin_password,
                                          connection_timeout=5, charset='utf8mb4')
    try:
        return provision(connection, recovery_password)
    finally:
        connection.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.apply:
        parser.error('Explicit --apply required; no administrator SQL run')
    try:
        print(json.dumps(run(), indent=2, sort_keys=True))
    except Exception as exc:
        print('Recovery provisioning stopped: ' + type(exc).__name__ +
              '. Inspect the target for partial DDL before any retry.')
        raise SystemExit(1)
