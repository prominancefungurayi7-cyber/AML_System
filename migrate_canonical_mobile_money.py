"""Explicit Stage2 additive migration; never import or start server.py.

Default: inspect only. --apply creates one new table and its indexes, without
backfill. Logical rollback: CANONICAL_MOBILE_MONEY_ENABLED=OFF; preserve the table
and any canonical rows. No destructive down migration is supplied.
"""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlparse, unquote
from dotenv import dotenv_values
from database import DatabaseAdapter
from canonical_mobile_money_store import inspect, migrate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--evidence',required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parent
    output=(root/args.evidence).resolve()
    allowed=(root/'ml_v4/evidence/integration_stage2').resolve()
    if output.parent != allowed or output.exists():
        raise ValueError('New Stage2 evidence path required')
    values=dotenv_values(root/'.env')
    url=os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL') or values.get('DATABASE_URL') or values.get('MYSQL_URL')
    if not url:
        raise ValueError('Explicit database configuration required')
    parsed=urlparse(url)
    if parsed.scheme not in ('mysql','mysql+mysqlconnector'):
        raise ValueError('Deployed CLI supports the audited MySQL engine only')
    import mysql.connector
    raw=mysql.connector.connect(host=parsed.hostname,port=parsed.port or 3306,
        user=unquote(parsed.username or ''),password=unquote(parsed.password or ''),
        database=parsed.path.lstrip('/'),connection_timeout=5)
    conn=DatabaseAdapter(raw,'mysql')
    result={'apply_requested':args.apply,'engine':'mysql','historical_rows_modified':False,
            'rollback':'Disable canonical ingestion; retain schema and rows. MySQL DDL auto-commits.'}
    try:
        result['runtime']=conn.execute('SELECT VERSION() AS version').fetchone()
        result['before']=inspect(conn)
        if args.apply:
            result['migration']=migrate(conn);conn.commit()
            result['repeat']=migrate(conn)
            assert not result['repeat']['changed']
        result['after']=inspect(conn)
        result['status']='PASS'
    except Exception as exc:
        conn.rollback()
        result['status']='FAIL';result['error_type']=type(exc).__name__
        # Do not log connection strings, credentials or raw database messages.
        raise
    finally:
        conn.close()
        output.write_text(json.dumps(result,indent=2,default=str)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
