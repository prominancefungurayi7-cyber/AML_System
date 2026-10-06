"""Development-only data access. Evaluation is a different entry point."""
from pathlib import Path
from stage16r_contract import ROOT

DEVELOPMENT_ROOT=ROOT/'ml_v4/data/development'
ALLOWED_FILES={'warmup_observables.csv','transactions.csv','ground_truth.csv'}


def development_path(partition,filename):
    if partition not in ('train','validation') or filename not in ALLOWED_FILES:
        raise PermissionError('Development access permits exact train/validation names and declared files only')
    root=DEVELOPMENT_ROOT.absolute()
    path=root/partition/filename
    if root.resolve()!=root or path.resolve()!=path or not path.resolve().is_relative_to(root):
        raise PermissionError('Symlink, alias or escaping development path rejected')
    return path


def load_development(partition,filename):
    return development_path(partition,filename).read_bytes()
