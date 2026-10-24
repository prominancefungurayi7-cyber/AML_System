"""Create the explicitly requested local Agent identity once; never reset it."""
import sys
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    from dotenv import dotenv_values
    from database import connect_db
    from werkzeug.security import generate_password_hash
    from v4_history_attestation import SERVER_UUID
    root = Path(__file__).resolve().parents[1]
    conn = connect_db(dotenv_values(root / '.env')['DATABASE_URL'])
    try:
        identity = conn.execute('SELECT DATABASE() db,@@server_uuid uuid,CURRENT_USER() principal').fetchone()
        if dict(identity) != dict(db='aml', uuid=SERVER_UUID, principal='aml@127.0.0.1'):
            raise RuntimeError('Local database identity mismatch')
        if conn.execute("SELECT GET_LOCK('aml_agent_provision_v1',5) acquired").fetchone()['acquired'] != 1:
            raise RuntimeError('Account provisioning busy')
        user = conn.execute("SELECT role,account_number FROM users WHERE username='Agent'").fetchone()
        agent = conn.execute("SELECT id,status FROM agents WHERE agent_code='AGENT0001'").fetchone()
        if user or agent:
            if user and agent and user['role'] == 'agent' and user['account_number'] == 'AGENT0001' and agent['status'] == 'active':
                print('Agent account and active record already exist; credentials unchanged.')
                return
            raise RuntimeError('Existing identity needs review; no changes made')
        if conn.execute('SELECT COUNT(*) n FROM agents').fetchone()['n']:
            raise RuntimeError('Agent records already exist; inspect before provisioning')
        before = conn.execute('SELECT COUNT(*) n,COALESCE(SUM(amount),0) total FROM transactions').fetchone()
        conn.execute('INSERT INTO users(username,email,id_number,password_hash,role,account_number,balance,created_at) '
            'VALUES (?,?,?,?,?,?,?,?)',('Agent','agent@example.com','00-0000001A00',
            generate_password_hash('Agent123'),'agent','AGENT0001',0,datetime.now(timezone.utc).isoformat()))
        conn.execute("INSERT INTO agents(agent_code,agent_name,status) VALUES ('AGENT0001','Agent','active')")
        after = conn.execute('SELECT COUNT(*) n,COALESCE(SUM(amount),0) total FROM transactions').fetchone()
        if dict(before) != dict(after):
            raise RuntimeError('Transaction totals changed during account provisioning')
        conn.commit()
        print('Created Agent login linked to AGENT0001. Electronic float: $0.00. No payments created.')
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
