"""Reproduce twice in temporary V2 storage, audit, then publish one V2 dataset."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

from contracts import ROOT, safe_path, digest, write_json, load_development
from dataset_generator import generate
from dataset_audit import audit


def protected_hashes():
    base=ROOT.parent
    paths=list(base.glob('*.py'))+[base/'requirements.txt',base/'Dockerfile',base/'railway.json',base/'Procfile']
    for name in ('data','ml','ml_archive','reports','tests','static','templates'):
        paths.extend(p for p in (base/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths.extend(p for p in base.glob('*.db') if p.is_file())
    return {p.relative_to(base).as_posix():digest(p) for p in sorted(set(paths)) if p.is_file()}


def hashes(folder):
    return {p.relative_to(folder).as_posix():digest(p) for p in sorted(folder.rglob('*')) if p.is_file()}


def main():
    destination=safe_path(ROOT/'data')
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError('Permanent V2 dataset exists; overwrite refused')
    for output in ('stage2_audit.json','stage2_reproducibility.json','stage2_v1_protection.json','stage2_tests.txt'):
        if (ROOT/'reports'/output).exists(): raise FileExistsError(output)
    before=protected_hashes()
    tmp=safe_path(ROOT/'tmp'); tmp.mkdir(exist_ok=True)
    tests=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(ROOT/'tests'),'-p','test_stage2*.py','-v'],capture_output=True,text=True)
    test_text=tests.stdout+tests.stderr
    print(test_text,flush=True)
    if tests.returncode: raise RuntimeError('Contract tests failed')
    start=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='stage2_',dir=tmp) as work:
        work=safe_path(work)
        print('Generating temporary run A...',flush=True)
        first=generate(work/'run_a')
        print('Auditing persisted run A...',flush=True)
        result=audit(first)
        if result['failures']:
            write_json(ROOT/'reports/stage2_failed_audit.json',result)
            raise RuntimeError(f"Independent audit failed: {result['failures']}")
        print('Generating temporary run B...',flush=True)
        second=generate(work/'run_b')
        hash_a,hash_b=hashes(first),hashes(second)
        if hash_a!=hash_b: raise RuntimeError('Deterministic reproducibility failed')
        print('All file hashes match. Publishing one permanent V2 dataset...',flush=True)
        # Destination is resolved, link-free, inside V2 and previously checked empty.
        if destination.exists() and any(destination.iterdir()): raise FileExistsError(destination)
        shutil.copytree(first,destination,dirs_exist_ok=True)
        if hashes(destination)!=hash_a: raise RuntimeError('Permanent copy hash mismatch')
        dev_train=load_development(destination,'train')
        dev_val=load_development(destination,'validation')
        if (len(dev_train),len(dev_val))!=(60000,15000): raise RuntimeError('Development loader validation failed')
        for p in ('final_test','independent'):
            try: load_development(destination,p)
            except PermissionError: pass
            else: raise RuntimeError('Holdout load was not denied')
        # Deliberate persisted-data tampering must be detected independently.
        probe=second/'development/train/transactions.csv'
        text=probe.read_text(encoding='utf-8')
        probe.write_text(text.replace(',USD,',',EUR,',1),encoding='utf-8',newline='')
        negative=audit(second)
        if not {'file_hash','currency'}.issubset(set(negative['failures'])):
            raise RuntimeError('Negative audit test did not detect tampering')
        reproducibility={'result':'PASS','seed':20260921,'runs':2,'all_files_identical':True,'file_count':len(hash_a),
            'file_hashes':hash_a,'transaction_order_ground_truth_entities_and_plans_identical':True,
            'permanent_copy_hashes_identical':True,'temporary_duplicates_removed_on_exit':True,
            'negative_tamper_test':'PASS: modified currency rejected by hash and semantic checks'}
    after=protected_hashes()
    protection={'result':'PASS' if before==after else 'FAIL','protected_file_count':len(before),
        'before_hashes':before,'after_hashes':after,
        'scope':'Application root Python/config/deployment files, V1 data/models/archive/reports/tests/static/templates and root databases; hashes only',
        'changed':[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)]}
    write_json(ROOT/'reports/stage2_audit.json',result)
    write_json(ROOT/'reports/stage2_reproducibility.json',reproducibility)
    write_json(ROOT/'reports/stage2_v1_protection.json',protection)
    with safe_path(ROOT/'reports/stage2_tests.txt').open('x',encoding='utf-8') as f: f.write(test_text)
    if before!=after: raise RuntimeError('V1 protection failed')
    print(f'Stage 2 structural audit PASS; reproducibility PASS; V1 hash protection PASS ({time.monotonic()-start:.1f}s)',flush=True)


if __name__=='__main__': main()
