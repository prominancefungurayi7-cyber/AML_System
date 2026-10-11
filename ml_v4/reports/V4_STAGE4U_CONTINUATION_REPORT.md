# MODEL V4 — STAGE 4U CONTINUATION AFTER MYSQL ADMIN PROVISIONING

**B — LOCAL CREDENTIAL BINDING REQUIRED BEFORE LIVE VERIFICATION**

The administrator reports that MySQL 8.0.46 now has `v4_stage4s_disposable`, account `v4_stage4t_runner` at `127.0.0.1`, server UUID `d441b7bb-43f6-11f1-a2d8-0a0027000005`, global USAGE and only the specified schema privileges. These are **administrator-supplied facts**. The dedicated test URL and expected UUID were absent from this Codex process, and the test authority file was absent. I could not authenticate to verify them or run the installer. No MySQL connection, schema write, scope creation, transaction or prediction occurred in this continuation.

## Prepared local verification

The [read-only live checker](../evidence/stage4u_continue/live_checks.py) verifies the actual database, server UUID, authenticated principal, exact scoped privilege set and MySQL version before any write. It requires the test database to be empty. It attempts to connect to `aml` using only the restricted **test** account and requires denial. It executes the unchanged production connector with the disposable URL and requires rejection before connection. It writes only sanitized evidence, with no password or URL.

After the guarded [schema installer](../evidence/stage4u/install_schema.py) and Stage4T `prepare`/`check`, the checker verifies all six exact trigger definitions, the pinned independent test boundary, genuine Stage2A empty-ledger assessment and freshness, empty parent/canonical/journal/result tables, and wrong-server/altered-boundary rejection. It does not remove or alter a trigger to manufacture a failure test. The original `aml` database is not used for fixtures or queried by this checker; denial of the test account's connection to `aml` is the direct isolation check. This cannot prove the prior contents of `aml` from within a credential-free session.

The [local PowerShell runner](../evidence/stage4u_continue/run_local.ps1) prompts securely for the test account password, percent-encodes it into the current process's dedicated test URL, runs preflight → schema installer → Stage4T `prepare` → Stage4T `check` → final verification, checks each exit code, and removes the test environment variables afterward. It does not print or store the password. The script's PowerShell syntax was checked without execution. It is intentionally separate from Flask and does not set `V4_SHADOW_ENABLED`.

Run the following **in a local PowerShell session in the workspace root**, after confirming the administrator provisioned the reported account. Do not paste the password into the command:

```powershell
& .\ml_v4\evidence\stage4u_continue\run_local.ps1
```

The runner stops at the first failed gate. MySQL DDL may auto-commit; if schema installation fails partway, inspect the disposable database before deciding on administrator cleanup and a fresh provision. Do not rerun blindly or reset `aml`.

Successful local execution creates `preflight_live.json` and `verification_live.json` under `ml_v4/evidence/stage4u_continue/` plus the ignored local `.stage4t_authority.json`. These files record server/database identity, principal, scoped privilege names, exact trigger names, boundary digest, attestation status and empty financial/result counts. The authority file contains no password but must remain bound to the local test environment. Report the sanitized evidence before Stage4S financial fixtures; do not infer readiness from the administrator statement alone.

## Status and preservation

The Stage4U schema-only SQL and reviewed hash are unchanged. The Stage4T test adapter, Stage3 approved source, frozen model and historical reports were not modified in this continuation. New writes are this report and the continuation checker, runner and evidence manifest. Frozen model SHA-256 remains `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`; 40 semantic fields, 42 estimator inputs and threshold 0.50 remain fixed. No sealed evaluation data, V1/V3 artifacts or ordinary application mode was accessed or altered.

**Stage4S end-to-end testing cannot yet resume on verified evidence.** It may resume after the local runner passes and its sanitized live evidence is reviewed. No financial fixture was submitted in Stage4U.

STAGE 4U CONTINUATION COMPLETE — WAITING FOR LOCAL VERIFICATION.
