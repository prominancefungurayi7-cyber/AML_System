# Read-only local readiness. Never installs schema or submits financial fixtures.
$ErrorActionPreference = 'Stop'
$stage4saRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$stage4saInferencePython = Join-Path $stage4saRoot 'ml_v4\.venv_inference_stage3\Scripts\python.exe'
$stage4saAppPython = Join-Path $stage4saRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $stage4saInferencePython) -or
    -not (Test-Path -LiteralPath $stage4saAppPython)) {
    throw 'Required isolated Python runtimes are unavailable.'
}
if ($env:V4_SHADOW_ENABLED -eq 'ON') { throw 'Ordinary V4 shadow mode must remain OFF.' }
if ($env:DATABASE_URL -or $env:MYSQL_URL) {
    throw 'Unset ordinary DATABASE_URL and MYSQL_URL before isolated testing.'
}
$stage4saSecret = Read-Host 'Password for v4_stage4t_runner only' -AsSecureString
$stage4saPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($stage4saSecret)
try {
    $stage4saPlain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($stage4saPointer)
    $stage4saEncoded = [Uri]::EscapeDataString($stage4saPlain)
    $env:V4_STAGE4T_TEST_DB_URL = "mysql://v4_stage4t_runner:$stage4saEncoded@127.0.0.1:3306/v4_stage4s_disposable"
    $env:V4_STAGE4T_EXPECTED_SERVER_UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
    $stage4saPlain = $null
    $stage4saEncoded = $null
    Push-Location $stage4saRoot
    try {
        & $stage4saInferencePython -I -B ml_v4/test_binding/v1.py check
        if ($LASTEXITCODE -ne 0) { throw 'Stage4T test binding check failed.' }
        & $stage4saInferencePython -I -B ml_v4/evidence/stage4sa/verify_live.py
        if ($LASTEXITCODE -ne 0) { throw 'Fresh MySQL isolation/history check failed.' }
        & $stage4saAppPython -B -m ml_v4.stage4sa.live_readiness
        if ($LASTEXITCODE -ne 0) { throw 'Flask harness readiness check failed.' }
        Write-Output 'Ready for a separate fixture stage. No financial fixtures were submitted.'
    } finally {
        Pop-Location
    }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($stage4saPointer)
    Remove-Item Env:V4_STAGE4T_TEST_DB_URL -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4T_EXPECTED_SERVER_UUID -ErrorAction SilentlyContinue
    $stage4saPlain = $null
    $stage4saEncoded = $null
    $stage4saSecret = $null
}
