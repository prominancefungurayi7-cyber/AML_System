# Stage4S-B: local, disposable-database-only fixture run.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$infer = Join-Path $root 'ml_v4\.venv_inference_stage3\Scripts\python.exe'
$app = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $infer) -or -not (Test-Path -LiteralPath $app)) { throw 'Isolated Python runtimes unavailable.' }
if ($env:DATABASE_URL -or $env:MYSQL_URL -or $env:V4_STAGE4T_TEST_DB_URL) { throw 'Unset all database URL variables before this run.' }
if ($env:V4_SHADOW_ENABLED -eq 'ON') { throw 'Production V4 shadow mode must remain OFF.' }
$secret = Read-Host 'Password for v4_stage4t_runner on disposable MySQL only' -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try {
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    $encoded = [Uri]::EscapeDataString($plain)
    $env:V4_STAGE4T_TEST_DB_URL = "mysql://v4_stage4t_runner:$encoded@127.0.0.1:3306/v4_stage4s_disposable"
    $env:V4_STAGE4T_EXPECTED_SERVER_UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
    $plain = $null
    $encoded = $null
    Push-Location $root
    try {
        & $infer -I -B ml_v4/test_binding/v1.py check
        if ($LASTEXITCODE -ne 0) { throw 'Binding identity/authority check failed.' }
        & $infer -I -B ml_v4/evidence/stage4sa/verify_live.py
        if ($LASTEXITCODE -ne 0) { throw 'Fresh live isolation/history check failed.' }
        & $app -B -m ml_v4.stage4sa.live_readiness
        if ($LASTEXITCODE -ne 0) { throw 'Approved harness and source/model readiness failed.' }
        & $app -B -m ml_v4.stage4sa.live_e2e
        if ($LASTEXITCODE -ne 0) { throw 'Live E2E failed; inspect evidence without activating V4.' }
    } finally { Pop-Location }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    Remove-Item Env:V4_STAGE4T_TEST_DB_URL -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4T_EXPECTED_SERVER_UUID -ErrorAction SilentlyContinue
    $plain = $null
    $encoded = $null
    $secret = $null
}
