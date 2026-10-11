# Stage4S-I. Read-only disposable checks. No ALTER, DML, fixtures or backup restore.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$python = Join-Path $root 'ml_v4\.venv_inference_stage3\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Isolated Python runtime unavailable.' }
if ($env:DATABASE_URL -or $env:MYSQL_URL -or $env:V4_STAGE4T_TEST_DB_URL) {
    throw 'Unset all database URL variables before disposable preflight.'
}
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
        & $python -B -m ml_v4.stage4sg.preflight
        if ($LASTEXITCODE -ne 0) { throw 'Disposable read-only preflight failed.' }
    } finally { Pop-Location }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    Remove-Item Env:V4_STAGE4T_TEST_DB_URL -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4T_EXPECTED_SERVER_UUID -ErrorAction SilentlyContinue
    $plain = $null
    $encoded = $null
    $secret = $null
}
