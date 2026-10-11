# Read-only inspection after an interrupted disposable retry-schema migration.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$app = Join-Path $root '.venv\Scripts\python.exe'
$infer = Join-Path $root 'ml_v4\.venv_inference_stage3\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $app) -or -not (Test-Path -LiteralPath $infer)) {
    throw 'Approved isolated Python runtimes unavailable.'
}
if ($env:DATABASE_URL -or $env:MYSQL_URL -or $env:V4_STAGE4T_TEST_DB_URL -or
    $env:V4_STAGE4SK_RECOVERY_DB_URL -or $env:STAGE5C_SCHEMA_APPLY) {
    throw 'Unset inherited database or schema variables.'
}
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
        if ($LASTEXITCODE -ne 0) { throw 'Disposable identity/authority check failed.' }
        & $app -B -m ml_v4.stage5c.inspect_retry_schema
        if ($LASTEXITCODE -ne 0) { throw 'Read-only retry schema inspection failed.' }
    } finally { Pop-Location }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    foreach ($name in @('V4_STAGE4T_TEST_DB_URL','V4_STAGE4T_EXPECTED_SERVER_UUID')) {
        Remove-Item "Env:$name" -ErrorAction SilentlyContinue
    }
    $plain = $null
    $encoded = $null
    $secret = $null
}
