"""Explicit local one-shot inference. No listener; no live application activation."""
import argparse,json,os
from pathlib import Path
from urllib.parse import urlparse,unquote
from .service import ROOT,infer

def connection():
    from dotenv import dotenv_values
    import mysql.connector
    from database import DatabaseAdapter
    env=dotenv_values(ROOT/'.env')
    url=os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL') or env.get('DATABASE_URL') or env.get('MYSQL_URL')
    p=urlparse(url or '')
    if p.scheme not in ('mysql','mysql+mysqlconnector') or p.path!='/aml': raise ValueError('Configured MySQL aml required')
    return DatabaseAdapter(mysql.connector.connect(host=p.hostname,port=p.port or 3306,user=unquote(p.username or ''),password=unquote(p.password or ''),database='aml',connection_timeout=5),'mysql')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--transaction-id',required=True,type=int)
    args=parser.parse_args()
    print(json.dumps(infer(connection,args.transaction_id),allow_nan=False))
