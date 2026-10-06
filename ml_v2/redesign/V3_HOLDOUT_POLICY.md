# V3 holdout policy — proposed revision 1

New V3 Final Test and Independent Evaluation streams must be generated independently of V2. The V2 holdouts were read as bytes during preliminary Stage 7 hashing, although no records or labels were parsed for analysis. Preserve that audit history; do not reuse those files as newly sealed V3 evaluation data. Stage 8 must not open, hash, list their contents, or derive any distribution from them.

## Roles and future storage separation

The future generator is a separately authorized offline program. It may materialize, validate and hash all newly generated partitions at generation time, then close them. It is not imported by training or feature-development programs. Development code must never create holdouts, even as a convenience to run an experiment.

Proposed future layout, documented here only:

| Area | Owner and access |
|---|---|
| `ml_v3/development/` | Train and Validation raw records, targets, features, model-development artifacts and logs. Development readers take a partition enum restricted to these two names. |
| `ml_v3/evaluation_store/` | New Final Test and Independent data and their private integrity manifest. Only generation-time validation and a later separately authorized evaluator know these paths. |
| `ml_v3/contracts/` | Frozen schema/version, development-only manifest and public generation certificate. Contains no holdout filenames, raw statistics, labels or exact alert counts. |
| `ml_v3/evaluation_entry/` | Evaluation-only code that resolves private storage after checking an authorized frozen artifact contract. Not a dependency of development modules. |

No directories are created in Stage 8. Software checks are a boundary against accidental access, not encryption, an external custodian or an OS guarantee against deliberate unrestricted reads.

## Generation-time integrity record

1. Before writing, commit the design revision, generator/evaluator source revisions, deterministic seeds and partition/entity plan. Use a new output version and exclusive creation; refuse overwrites.
2. During generation, stream each file through SHA-256 as it is written. Within the same authorized generation phase, independently verify structural checks, accounting, temporal safety and entity isolation. If a reread is required for that verification, it belongs to the generation entry point before sealing, never to development code.
3. Store a private integrity manifest in the evaluation store with file paths, content digests, schema versions and audit details. Publish a **content commitment** to the canonical private manifest plus an opaque partition identifier and a generation-check pass indicator. The public certificate exposes no holdout label counts, features, examples or distributional diagnostics.
4. Store the canonical public-certificate digest in the frozen experiment registry/approved generation record. Development verifies that its local certificate matches this pinned digest and the declared dataset/schema versions, and verifies development file digests only. It does not follow a holdout pointer or reopen files to “verify” their digests.
5. Close the holdout store. Routine checksums, backups for development experiments, directory inventories and dataset summaries must use explicit development allowlists, not a recursive walk of the dataset root.

Checking a manifest or its commitment does **not** establish that unread holdout bytes have remained unchanged since sealing. It establishes the committed generation identity and protects the metadata comparison. Actual content integrity is rechecked only by the separately authorized evaluator when it is first allowed to open those files. State this limit plainly; do not claim to detect post-generation file corruption without reading the data. No cryptographic signature or stronger authenticity claim is assumed merely because SHA-256 is used.

## Development access contract

- The development loader accepts only `train` and `validation`; no override or generic arbitrary-file option exists. Reject evaluation partition names before resolving or opening a path.
- Root resolution uses explicit permitted directories, checks lexical and resolved ancestry, and rejects symlinks/junctions/reparse-point paths at every traversed component. It never enumerates a forbidden directory to decide whether it is forbidden.
- Hash/protection utilities accept an allowlist of development files and named immutable code/results. They must not import the old `v2_inputs()` helper or any helper that walks an entire raw-data root. Hashing is a data read and is subject to the same access rule.
- Feature and training packages do not import evaluation modules, holdout constants, generation entry points or private manifests. Audit logs contain opened development paths and purposes, with no automatic filesystem inventory.
- Test the denial paths with temporary synthetic sentinel fixtures outside the allowed development directory. A reader/hash attempted against the sentinel must fail before byte access. Never use real holdout files as test fixtures for the guard.
- Statically inspect imports and approved file-access entry points. In an authorized implementation, a runtime audit hook or equivalent test harness should fail disallowed open calls. These are additional checks, not claims that arbitrary Python code cannot bypass a software policy.

## Authorized later evaluation

The evaluator requires an explicit approval record and a frozen contract containing model bytes/digest, ordered feature names/formulas, preprocessing fit state, threshold/calibration, code/runtime versions and public generation certificate. It validates those before opening the private manifest. It then verifies actual content digests, computes causal histories separately inside each holdout, and produces the predefined evaluation report. Neither new fitting nor threshold selection is allowed on either holdout.

Final Test is used once for confirmatory assessment, followed by Independent Evaluation with the same frozen model and semantics. A bad score, content-integrity failure, or implementation issue does not authorize trying another model on the same holdout. Record the outcome and obtain a new explicitly versioned research authorization where necessary. Evaluation code may generate necessary holdout features only in this evaluation phase and must not feed them back into development.
