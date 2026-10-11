# Resume only the verified 15-table, zero-trigger disposable test state.
# Do not run the original installer or Stage4T prepare on this partial schema.
$ErrorActionPreference = 'Stop'
$recoveryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$recoveryPython = Join-Path $recoveryRoot 'ml_v4\.venv_inference_stage3\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $recoveryPython)) { throw 'Isolated inference Python is unavailable.' }
$recoverySecret = Read-Host 'Password for v4_stage4t_runner only' -AsSecureString
$recoveryPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($recoverySecret)
try {
    $recoveryPlain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($recoveryPtr)
    $recoveryEncoded = [Uri]::EscapeDataString($recoveryPlain)
    $env:V4_STAGE4T_TEST_DB_URL = "mysql://v4_stage4t_runner:$recoveryEncoded@127.0.0.1:3306/v4_stage4s_disposable"
    $env:V4_STAGE4T_EXPECTED_SERVER_UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
    $recoveryPlain = $null
    $recoveryEncoded = $null

    Push-Location $recoveryRoot
    try {
        & $recoveryPython -I -B ml_v4/evidence/mysql_test_recovery/recover_partial.py
        if ($LASTEXITCODE -ne 0) { throw 'Recovery stopped. Inspect the disposable database before any retry.' }

        & $recoveryPython -I -B ml_v4/test_binding/v1.py check
        if ($LASTEXITCODE -ne 0) { throw 'Test authority check failed.' }

        & $recoveryPython -I -B ml_v4/evidence/stage4u_continue/live_checks.py verify
        if ($LASTEXITCODE -ne 0) { throw 'Final isolation/history verification failed.' }

        Write-Output 'Disposable MySQL recovery verified. No financial fixtures were submitted.'
    } finally {
        Pop-Location
    }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($recoveryPtr)
    Remove-Item Env:V4_STAGE4T_TEST_DB_URL -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4T_EXPECTED_SERVER_UUID -ErrorAction SilentlyContinue
    $recoveryPlain = $null
    $recoveryEncoded = $null
    $recoverySecret = $null
}
