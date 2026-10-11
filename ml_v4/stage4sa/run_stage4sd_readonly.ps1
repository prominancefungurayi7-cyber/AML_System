# Stage4S-D: existing records only. No fixture submission or database migration.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$infer = Join-Path $root 'ml_v4\.venv_inference_stage3\Scripts\python.exe'
$app = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $infer) -or -not (Test-Path -LiteralPath $app)) {
    throw 'Required isolated Python runtimes unavailable.'
}
if ($env:DATABASE_URL -or $env:MYSQL_URL -or $env:V4_STAGE4T_TEST_DB_URL) {
    throw 'Unset all database URL variables before isolated verification.'
}
if ($env:V4_SHADOW_ENABLED -eq 'ON') { throw 'Ordinary V4 shadow mode must remain OFF.' }
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
        if ($LASTEXITCODE -ne 0) { throw 'Disposable identity/grants/trigger/authority check failed.' }
        & $app -B -m ml_v4.stage4sa.stage4sd_live
        if ($LASTEXITCODE -ne 0) { throw 'Read-only Flask/legacy probe failed.' }
        & $infer -B -m ml_v4.stage4sa.stage4sd_v4_replay
        if ($LASTEXITCODE -ne 0) { throw 'Read-only frozen V4 replay failed.' }
        Write-Output 'Stage4S-D read-only verification PASS. No financial fixture submitted.'
    } finally { Pop-Location }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    Remove-Item Env:V4_STAGE4T_TEST_DB_URL -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4T_EXPECTED_SERVER_UUID -ErrorAction SilentlyContinue
    $plain = $null
    $encoded = $null
    $secret = $null
}
