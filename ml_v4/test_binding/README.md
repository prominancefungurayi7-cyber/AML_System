# Stage4T isolated MySQL test binding

Version `v4.test_binding.stage4t.1` is a separate test deployment adapter. Flask and the Stage4R production worker never import or select it. The approved Stage3 connector, history gate, service and tests remain unchanged. The adapter calls the same frozen `FrozenModel.replay`, `predict` and probability decision methods after its own test database authority and Stage2A history verification.

The adapter uses only `V4_STAGE4T_TEST_DB_URL`; it does not read `.env`, `DATABASE_URL` or `MYSQL_URL`. Its database and user are fixed as `v4_stage4s_disposable` and `v4_stage4t_runner`. It rejects global or other database grants, unexpected server UUID, missing/changeable boundary, capture trigger mismatch and stale/incomplete history. `.stage4t_authority.json` is generated only by `prepare` after a genuine empty database boundary and Stage2A initial attestation. It contains no password and is excluded from source control. Keep it local to the isolated test environment.

Administrator provisioning is required before use. See the Stage4T report for the exact SQL handoff and schema requirements. Set the two dedicated environment variables only in the disposable test process. Then run from the repository root:

```powershell
.\ml_v4\.venv_inference_stage3\Scripts\python.exe -I -B ml_v4/test_binding/v1.py prepare
.\ml_v4\.venv_inference_stage3\Scripts\python.exe -I -B ml_v4/test_binding/v1.py check
```

The `prepare` action has no reset mode. It refuses preexisting canonical/history tables or transactions and writes only after checking database, server, principal, grants and reviewed application schema. If interrupted after schema changes, inspect the disposable database and decide a new provisioned database identity; do not force a fabricated authority record.

For a future controlled test, `worker.py` accepts the same three command arguments as the Stage4R child: transaction ID, committed canonical row digest and server UUID. It requires the committed parent/canonical insert journal, performs Stage2A technical reassessment under the history lock, and then calls the separate test inference adapter on a fresh snapshot. This child is never selected by an HTTP request or the ordinary application's environment flag. Stage4S must explicitly bind its isolated test harness to it after provisioning and verify actual MySQL behavior.

The test adapter returns the same versioned model result shape but its deployment connector/history gate are new source. This is **not** byte-identical execution of Stage3's `infer` function. It reuses the unchanged frozen model operations and the unchanged Stage2A causal verifier.
