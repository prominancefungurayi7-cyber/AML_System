"""Privileged local prototype-state command; never start Flask or load a model.

Commands: inspect, migrate, establish, attest, revise. Changes require explicit
arguments. Credentials are read locally, never logged. No browser endpoint exists.
MySQL named lock serializes commands; each assessment uses REPEATABLE READ snapshot.
"""
import argparse
import getpass
import json
import os
from pathlib import Path
from urllib.parse import urlparse,unquote
from dotenv import dotenv_values
from database import DatabaseAdapter
from canonical_history import digest,freshness
from canonical_history_store import migrate,create_scope,attest,revise_scope,assess,current_scope
from canonical_history_journal import ensure as ensure_journal


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['inspect','migrate','establish','attest','revise'])
    parser.add_argument('--scope',default='controlled-prototype-v1')
    parser.add_argument('--reference',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--resolutions',help='Local reviewed JSON ID -> authoritative resolution reference')
    args=parser.parse_args()
    root=Path(__file__).resolve().parent
    out=(root/args.output).resolve()
    if out.parent!=(root/'ml_v4/evidence/integration_stage2a').resolve() or out.exists():
        raise ValueError('New Stage2A evidence file required')
    env=dotenv_values(root/'.env')
    url=os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL') or env.get('DATABASE_URL') or env.get('MYSQL_URL')
    p=urlparse(url or '')
    if p.scheme not in ('mysql','mysql+mysqlconnector'): raise ValueError('Audited MySQL required')
    import mysql.connector
    raw=mysql.connector.connect(host=p.hostname,port=p.port or 3306,user=unquote(p.username or ''),password=unquote(p.password or ''),database=p.path.lstrip('/'),connection_timeout=5)
    c=DatabaseAdapter(raw,'mysql')
    result={'command':args.command,'claim':'Controlled prototype only; not real operator history or independent custody'}
    def protected():
        # Audit fingerprints only; no customer values exported into evidence.
        return {t:digest([dict(r) for r in c.execute('SELECT * FROM '+t+' ORDER BY '+key).fetchall()])
                for t,key in (('transactions','id'),('canonical_mobile_money_events','transaction_id'))}
    try:
        result['engine']=c.execute('SELECT VERSION() AS version').fetchone()
        lock=c.execute("SELECT GET_LOCK('cmm_history_admin_v1',5) AS acquired").fetchone()['acquired']
        if lock!=1: raise RuntimeError('Admin verifier lock unavailable')
        result['tables_before']={}
        for table in ('transactions','canonical_mobile_money_events','cmm_observation_scopes','cmm_history_attestations','cmm_entity_history','cmm_source_changes'):
            exists=c.execute('SHOW TABLES LIKE ?', (table,)).fetchone()
            if exists:
                result['tables_before'][table]=[dict(r) for r in c.execute('SHOW COLUMNS FROM '+table).fetchall()]
        before=protected();c.commit()
        if args.command=='migrate':
            result['created']=migrate(c);c.commit()
            result['journal']=ensure_journal(c,apply=True);c.commit()
            ensure_journal(c)
            result['idempotent_repeat']=migrate(c);c.commit()
            assert result['idempotent_repeat']==[]
        elif args.command!='inspect':
            c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
            c.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT')
            authority='local-admin-command:'+getpass.getuser()
            if args.command=='establish':
                result['scope']=create_scope(c,args.scope,authority,args.reference)
            elif args.command=='revise':
                result['scope']=revise_scope(c,args.scope,authority,args.reference)
            else:
                resolutions=json.loads(Path(args.resolutions).read_text()) if args.resolutions else None
                a=attest(c,args.scope,authority,args.reference,resolutions)
                # Detailed per-entity evidence stays in controlled DB state.
                result['attestation']={k:v for k,v in a.items() if k not in ('fingerprint','protected_fingerprint','entities')}
            c.commit()
        else:
            try:
                result['journal']=ensure_journal(c)
                result['journal_ready']=True
            except ValueError as exc:
                result['journal_ready']=False
                result['journal_error']=str(exc)
            c.commit()
            if 'cmm_observation_scopes' in result['tables_before'] and current_scope(c,args.scope):
                c.commit()
                c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
                c.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT')
                s,a,previous=assess(c,args.scope)
                result['current_status']=freshness(s,a,previous)
                result['issues']=a['issues'];result['scope']=s
                c.rollback()
            else:
                result['scope']=None;result['current_status']='UNKNOWN'
                c.rollback()
        after=protected();c.rollback()
        result['source_before_sha256']=before;result['source_after_sha256']=after
        result['source_unchanged']=before==after
        if before!=after: raise RuntimeError('Concurrent source revision; not a preservation PASS')
        result['status']='PASS'
    except Exception as exc:
        c.rollback();result['status']='FAIL';result['error_type']=type(exc).__name__;result['error_number']=getattr(exc,'errno',None)
        raise
    finally:
        try:
            c.execute("SELECT RELEASE_LOCK('cmm_history_admin_v1')")
        finally:
            c.close()
            out.write_text(json.dumps(result,indent=2,default=str)+'\n',encoding='utf-8')


if __name__=='__main__': main()
