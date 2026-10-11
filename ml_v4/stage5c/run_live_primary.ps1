# Guarded Stage5C disposable Flask/MySQL verification. Creates synthetic test rows.
param(
    [switch]$InspectOnly,
    [switch]$FinishReadOnly,
    [switch]$Execute,
    [switch]$StartNewAfterReview,
    [ValidateSet('On','Off')][string]$RuleEngine
)
$ErrorActionPreference = 'Stop'
if ($InspectOnly -or $FinishReadOnly) {
    if ($Execute -or $StartNewAfterReview -or $RuleEngine) {
        throw 'Read-only inspection cannot be combined with execution options.'
    }
} elseif (-not ($Execute -and $StartNewAfterReview -and $RuleEngine)) {
    throw 'Run -InspectOnly first. New fixtures require -Execute -StartNewAfterReview -RuleEngine On|Off.'
}
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$app = Join-Path $root '.venv\Scripts\python.exe'
$infer = Join-Path $root 'ml_v4\.venv_inference_stage3\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $app) -or -not (Test-Path -LiteralPath $infer)) {
    throw 'Approved isolated Python runtimes unavailable.'
}
if ($env:DATABASE_URL -or $env:MYSQL_URL -or $env:V4_STAGE4T_TEST_DB_URL -or
    $env:V4_STAGE4SK_RECOVERY_DB_URL) {
    throw 'Unset all existing database URLs before this isolated test.'
}
if ($env:V4_SHADOW_ENABLED -eq 'ON') { throw 'Production shadow mode must remain OFF.' }
if ($env:AML_PRIMARY_MODEL) { throw 'Unset AML_PRIMARY_MODEL before this isolated test.' }
if ($env:STAGE5C_INJECT_POST_ATTEST_ERROR) { throw 'Unset inherited Stage5C worker fault injection.' }
$secret = Read-Host 'Password for v4_stage4t_runner on disposable MySQL only' -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try {
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    $encoded = [Uri]::EscapeDataString($plain)
    $env:V4_STAGE4T_TEST_DB_URL = "mysql://v4_stage4t_runner:$encoded@127.0.0.1:3306/v4_stage4s_disposable"
    $env:V4_STAGE4T_EXPECTED_SERVER_UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
    $env:AML_PRIMARY_MODEL = 'V4'
    $env:STAGE5C_EXECUTE = 'YES'
    if ($Execute) { $ruleSetting = $RuleEngine.ToLowerInvariant() }
    $plain = $null
    $encoded = $null
    Push-Location $root
    try {
        & $infer -I -B ml_v4/test_binding/v1.py check
        if ($LASTEXITCODE -ne 0) { throw 'Disposable binding identity/authority check failed.' }
        if ($InspectOnly) {
            & $app -B -m ml_v4.stage5c.live_primary --inspect-only
            if ($LASTEXITCODE -ne 0) { throw 'Read-only Stage5C reconciliation failed; no fixture submitted.' }
        } elseif ($FinishReadOnly) {
            & $app -B -m ml_v4.stage5c.finish_readonly
            if ($LASTEXITCODE -ne 0) { throw 'Read-only Stage5C final checks failed; no fixture submitted.' }
        } else {
            & $app -B -m ml_v4.stage5c.live_primary --execute --start-new-after-review --rule-engine $ruleSetting
            if ($LASTEXITCODE -ne 0) { throw 'Stage5C test incomplete; inspect local evidence before any retry.' }
        }
    } finally { Pop-Location }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    Remove-Item Env:V4_STAGE4T_TEST_DB_URL -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4T_EXPECTED_SERVER_UUID -ErrorAction SilentlyContinue
    Remove-Item Env:AML_PRIMARY_MODEL -ErrorAction SilentlyContinue
    Remove-Item Env:STAGE5C_EXECUTE -ErrorAction SilentlyContinue
    Remove-Item Env:STAGE5C_INJECT_POST_ATTEST_ERROR -ErrorAction SilentlyContinue
    $plain = $null
    $encoded = $null
    $secret = $null
}
