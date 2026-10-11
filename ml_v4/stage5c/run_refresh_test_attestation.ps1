# One-time Stage5C test-history attestation; disposable MySQL only.
param([switch]$Apply)
$ErrorActionPreference = 'Stop'
if (-not $Apply) { throw 'Explicit -Apply required. No database write was attempted.' }
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$app = Join-Path $root '.venv\Scripts\python.exe'
$infer = Join-Path $root 'ml_v4\.venv_inference_stage3\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $app) -or -not (Test-Path -LiteralPath $infer)) {
    throw 'Approved isolated Python runtimes unavailable.'
}
if ($env:DATABASE_URL -or $env:MYSQL_URL -or $env:V4_STAGE4T_TEST_DB_URL -or
    $env:V4_STAGE4SK_RECOVERY_DB_URL -or $env:AML_PRIMARY_MODEL) {
    throw 'Unset all existing database/model URL variables before this isolated repair.'
}
if ($env:V4_SHADOW_ENABLED -eq 'ON') { throw 'V4 shadow mode must remain OFF.' }
$secret = Read-Host 'Password for v4_stage4t_runner on disposable MySQL only' -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try {
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    $encoded = [Uri]::EscapeDataString($plain)
    $env:V4_STAGE4T_TEST_DB_URL = "mysql://v4_stage4t_runner:$encoded@127.0.0.1:3306/v4_stage4s_disposable"
    $env:V4_STAGE4T_EXPECTED_SERVER_UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
    $env:STAGE5C_ATTEST_EXECUTE = 'YES'
    $plain = $null
    $encoded = $null
    Push-Location $root
    try {
        & $infer -I -B ml_v4/test_binding/v1.py check
        if ($LASTEXITCODE -ne 0) { throw 'Pinned disposable binding/authority check failed.' }
        & $app -B -m ml_v4.stage5c.refresh_test_attestation --apply
        if ($LASTEXITCODE -ne 0) {
            throw 'Attestation refresh failed. Inspect read-only before any retry.'
        }
    } finally { Pop-Location }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    Remove-Item Env:V4_STAGE4T_TEST_DB_URL -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4T_EXPECTED_SERVER_UUID -ErrorAction SilentlyContinue
    Remove-Item Env:STAGE5C_ATTEST_EXECUTE -ErrorAction SilentlyContinue
    $plain = $null
    $encoded = $null
    $secret = $null
}
