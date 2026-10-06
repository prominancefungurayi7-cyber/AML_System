"""Explicit local migration/retry command; never imports Flask startup."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['migrate','retry'])
    parser.add_argument('--transaction-id',type=int)
    args=parser.parse_args()
    # CLI connection helper imports no ML/runtime code except safe service definitions.
    from ml_v4.frozen_inference.cli import connection
    from v4_shadow import migrate,process
    if args.action=='migrate':
        c=connection()
        try:
            changed=migrate(c);c.commit()
            print(json.dumps({'changed':changed}))
        finally:c.close()
    else:
        if args.transaction_id is None:parser.error('--transaction-id required')
        result=process(connection,args.transaction_id,lambda _:None)
        print(json.dumps(result,allow_nan=False))
