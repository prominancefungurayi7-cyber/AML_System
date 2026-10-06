# Model V2 research workspace

Stage 2 is isolated, standard-library-only Python (verified with Python 3.14.3).
No application imports, feature construction, model training or integration.

The approved Stage 2 request supersedes Stage 1's external custodian requirement.
`data/holdout/final_test` and `data/holdout/independent` are HOLDOUT partitions.
This is software separation, **not** encryption, OS isolation or protection from
someone deliberately opening the files with unrestricted Python/filesystem access.

Future development/training code must use `src/contracts.py:load_development`.
It accepts only `train` and `validation`, verifies manifest role and file hashes,
rejects links/junctions and provides no holdout override. Direct filesystem reads
of holdouts are prohibited in development code. Episode plans, commitments,
ground truth, entity profiles and identifiers are not model features. A later
approved evaluation entry point must require a frozen model/feature/threshold contract.

The generator and audit CLI can read all partitions solely for model-free
generation and structural verification. Do not use them to explore holdout
distributions for development.

Commands from the repository root:

```powershell
python -B -m unittest discover -s ml_v2/tests -p 'test_stage2*.py' -v
python -B ml_v2/src/dataset_audit.py --dataset ml_v2/data --report ml_v2/reports/new_audit.json
```

`src/run_stage2.py` refuses an existing permanent dataset. It generates twice
inside temporary V2 storage, compares every file hash, independently audits,
validates guards and preserves one permanent dataset. All writers reject output
paths outside this V2 root and refuse existing files. Do not run archived V1 tools.

The standalone interpreter uses no third-party dependencies and does not modify
the application's `.venv` or `requirements.txt`. Nothing here deploys the application.
