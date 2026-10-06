# MODEL V4 — STAGE 16V INDEPENDENT CUSTODY PROVISIONING AND VERIFICATION

**C — INDEPENDENT CUSTODY UNAVAILABLE.**

The available local infrastructure is controlled by the developer/workspace administrator. No independently administered endpoint, operator or delegated infrastructure access was supplied or verified. Stage 16V completed the local audit and a nonsecret durable-authorization fixture. It did not provision production custody. This conclusion applies to the infrastructure available in this session, not to the feasibility of obtaining an external custodian.

## 1. Authority and scope

Stage 15 defines the frozen predicates, feature and historical contracts; Stage 15A supplies its explicit amendments. Stage 16R's retained production draw and Stage 16S's support-failure decision remain historical evidence. Stage 16T requires independent challenge custody and Stage 16U explicitly leaves that gate blocked. Their applicable design, public evidence and implementation records were inspected. The original Final Test and Independent Evaluation remain SEALED_QUARANTINED, with public support-policy FAIL certificates. No private counts were requested or inferred.

No target, population, feature, support, metric or access policy was amended. No challenge data, candidate schedule, production salt, model feature, model fit or threshold was created. No sealed evaluation tree was enumerated, read, decrypted or hashed. No account, ACL, service, firewall or remote resource was changed.

## 2. Environment and administrator boundary

The recorded commands and outputs are in [environment_audit.json](../evidence/stage16v/environment_audit.json).

| Observation | Evidence and consequence |
| --- | --- |
| Execution identity | `PROE\CodexSandboxOffline`, SID ending 1003; medium integrity, Users and CodexSandboxUsers membership; no Administrators membership in this token |
| Local accounts | Administrator (disabled), CodexSandboxOffline, CodexSandboxOnline, DefaultAccount (disabled), Guest (disabled), PROMINENT, WDAGUtilityAccount (disabled) |
| Administrators | `PROE\Administrator` and `PROE\PROMINENT` |
| Workspace owner | `PROE\PROMINENT` |
| Workspace ACL | Shared sandbox group has Modify; owner, Administrators and SYSTEM have FullControl |
| Logging/service observations | EventLog running; WinRM stopped. Neither establishes independent logging or a remote custody service |
| Secret-management discovery | `Get-Secret` and `Get-SecretVault` commands unavailable in this session; this does not prove that no other secret service exists |

The restricted sandbox token does not make the host independent of its developer administrator. A new folder, local account or database under this ownership would not resolve administrator control, backup access, rollback or plaintext access. No separate operator with no model-selection role was identified. An infrastructure clarification was requested; no usable independently administered endpoint was available at report time. No credentials were sought.

## 3. Protected runtime, secrets and private registry

Production runtime, secret store and private ID registry: **NOT PROVISIONED / NOT VERIFIED**. Existing current-user DPAPI is explicitly insufficient under Stage 16T. No vault contents, credentials, private IDs or old encrypted envelope were inspected. Production entrypoints in Stage 16U remain fail-closed; this stage did not enable them.

The following is the required deployment specification, not installed infrastructure:

| Resource | Independent administrator action | Required verification |
| --- | --- | --- |
| Custodian host or isolated tenant | Assign an operator outside model selection; exclude developer host/tenant administrators, recovery identities and backup readers from custody administration | Record owner, operator, IAM/ACL exports and recovery/backup administration; verify both identities |
| Execution identity | Dedicated noninteractive service identity, fixed source release and fixed command; no developer-controlled paths or arbitrary code submission at execution | Custodian can run fixture command; developer cannot execute, replace source or impersonate service |
| Private storage | Custodian-only plaintext, scratch, output and backups; no developer mounts or shared working directory | Custodian can create/read/delete a disposable nonsecret probe; developer cannot list/read/write/delete it or change its ACL |
| Secret storage | Custodian-controlled vault/key policy, recovery and audit administration separated from developer | Test with a clearly nonsecret probe only; developer denied read/export/policy changes; no production salt yet |
| Private ID registry | Custodian-only registry and narrowly scoped collision-check operation; resolve old-registry access under its existing authority | Use dummy IDs to test allowed custodian operation and denied developer access; do not export or inspect old IDs in this stage |
| Authorization register | Independent transactional service keyed by study/protocol release, unique authorization, atomic irrevocable consume before any RNG or write | One winner under concurrency; denial after restart, crash, duplicate request and failure; no replacement authorization for the same draw |
| Access log | Independent append-only collector or retention-locked store; execution identity can append but cannot rewrite/delete; developer cannot administer retention | Verify reads/appends by authorized roles, rejected edits/deletes/truncation, delivery failure handling and independent retention configuration |

Log request identity, scope, UTC, authorization ID, frozen source/environment/protocol hashes, operation and outcome. Tie consumption durably to the audit record; fail closed if authorization or required logging cannot be committed. Consumed/failed draws remain terminal. Protect register backups and disaster recovery against restoring an unconsumed state. A hash chain alone is insufficient when the same operator can rewrite the chain and its root.

## 4. Access-control results

| Test | Result |
| --- | --- |
| Current identity reads declared public/source artifacts | SUCCESS |
| Current identity creates Stage 16V files and nonsecret fixture database | SUCCESS; demonstrates developer write access, not independent custody |
| Custodian identity accesses protected probe | NOT_RUN: identity and protected endpoint unavailable |
| Developer denied protected storage/secret/registry access | NOT_RUN: no independent resource to test |
| Developer denied admin, recovery, source replacement and log mutation | NOT_RUN: no independent resource to test |
| Independent append-only collector rejects mutation | NOT_RUN |

No denied fixture state transition is described as an OS/IAM denial. Both-identity verification remains mandatory before readiness can pass. Locally impersonating an account would not supply missing independent administration.

## 5. Restart-safe authorization fixture

[stage16v_fixture.py](../generation/stage16v_fixture.py) is a new, explicitly nonproduction SQLite fixture. It has no generator, evaluator, RNG, dataset or secret interface. A fixed `NONSECRET_TEST_ONLY` row, unique primary key, `BEGIN IMMEDIATE` transaction and conditional state update implement an authorization/consumption test. Each invocation is a separate process.

[authorization_fixture.json](../evidence/stage16v/authorization_fixture.json) records:

- Consumption before authorization: DENIED.
- First authorization: ALLOWED.
- Eight competing consumption processes: exactly one ALLOWED, seven DENIED.
- Reauthorization and consumption in later processes: both DENIED.

The fixture passes ordinary process-restart and contention checks. Committed consumption has no reset or retry operation, including after a caller exits without finishing. Power-loss and transactional-service disaster recovery were not tested. The local database and audit table can be deleted, edited or rolled back by the developer; therefore neither is an independently durable authorization service or append-only log. The temporary database was removed after testing. Production one-draw verification remains **BLOCKED**, despite fixture success.

## 6. Reproducibility and environment freeze

[reproducibility_readiness.json](../evidence/stage16v/reproducibility_readiness.json) records Windows 11 build 26200, Python 3.14.3, NumPy 2.4.3, SQLite 3.50.4 and the interpreter executable hash. These match Stage 16U's Python/NumPy reference pin. No candidate stream was instantiated. Stage 16U's saved fixture evidence was inspected; its full implementation suite was not rerun here because no generator code changed.

An installed-version observation is not a deployment lock. The external custodian must capture exact OS/runtime image, source release, wheel hashes and transitive dependencies, offline installation procedure, hardware, thread settings, UTC/locale, random-call ordering and serialization. Run the frozen hand fixtures in that environment and freeze it before any draw. Production salt creation and same-salt byte replay are later authorized in-custody operations. No production environment or replay is certified by this report.

## 7. Historical protection gap and preservation

All **47** declared artifact checks match: Stage 15 (20), Stage 15A (7), Stage 16T (10), Stage 16U (10). The explicit before/after inventory covers **62** unique design, public evidence, report, source and integration paths, with no changed paths. See [preservation_verification.json](../evidence/stage16v/preservation_verification.json). This is not a full-disk inventory or a fresh hash verification of unread dataset/evaluation bytes.

The unchanged Stage 15A validator was rerun and still exits 1 because `ml_archive/models/aml_ai_model.pkl` is absent from this working tree. Its exact Git HEAD blob is available and matches the historical expected SHA-256:

`55d6ab827505336fa930fd7110c030da4ccd7a389048a4064ca2ef04440352a0`.

Only those named archive bytes were hashed; no model was loaded. [historical_snapshot_gap.json](../evidence/stage16v/historical_snapshot_gap.json) preserves the failure and comparison. This identifies a verified recovery source for the first missing file. It does not prove that every later inventory entry exists or matches. No checkout deletion was reversed and no historical artifact, hash expectation or validator was edited.

To close the gap, the preservation operator must reconstruct the complete historical inventory from verified sources in a separate preservation checkout and run the unchanged validator there. Keep later authorized changes, including the V3 integration, in their own recorded revision; do not overwrite current application code to force an older manifest to pass. Until the full check succeeds, broad Stage 15A preservation remains incomplete. This limitation is not waived for production readiness.

Only new Stage 16V report/evidence and the two Stage 16V audit/fixture source files were written. V1/V2/V3, Flask, V4 data, frozen specifications and existing stage artifacts were not modified.

## 8. Remaining risks and required external actions

1. Supply an independently administered host/tenant and responsible custodian with no model-selection role, plus nonsecret endpoint and explicit delegated provisioning authority.
2. Deploy the storage, secret, registry, transactional authorization and independent log controls specified above. Local developer-administered infrastructure is insufficient.
3. Test the complete access matrix under genuine developer and custodian identities; retain independently verifiable evidence, including administration and recovery paths.
4. Test restart, concurrency, failure retention and rollback resistance in the actual service using nonsecret fixtures. Local fixture results are not portable custody certification.
5. Complete historical preservation recovery and independently freeze the final environment/source release. Preserve all failed checks and earlier decisions.
6. Obtain a separate readiness review and explicit generation authorization after all gates pass.

No supplied independent infrastructure can currently be configured, so installing local controls would not justify decision A or B. Absence of a supplied remote endpoint is an availability limitation, not a claim that the user's organization has no external resources.

## 9. Final decision

**C — INDEPENDENT CUSTODY UNAVAILABLE.**

This stage supplies an audit, a tested nonsecret authorization fixture and a concrete external provisioning specification. It does not authorize generation or relaxation of any gate. Production challenge generation, production salt creation, feature construction, fitting, threshold work and challenge evaluation remain blocked. Existing evaluation protections remain unchanged.

V4 STAGE 16V COMPLETE — WAITING FOR APPROVAL.
