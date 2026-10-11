# Run only in a local PowerShell session after administrator provisioning.
# The password is entered interactively and never written to project files.
$ErrorActionPreference = 'Stop'
$stage4uRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$stage4uPython = Join-Path $stage4uRoot 'ml_v4\.venv_inference_stage3\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $stage4uPython)) { throw 'Isolated inference Python is unavailable.' }
$stage4uSecret = Read-Host 'Password for v4_stage4t_runner only' -AsSecureString
$stage4uPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($stage4uSecret)
try {
    $stage4uPlain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($stage4uPtr)
    $stage4uEncoded = [Uri]::EscapeDataString($stage4uPlain)
    $env:V4_STAGE4T_TEST_DB_URL = "mysql://v4_stage4t_runner:$stage4uEncoded@127.0.0.1:3306/v4_stage4s_disposable"
    $env:V4_STAGE4T_EXPECTED_SERVER_UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
    $stage4uPlain = $null
    $stage4uEncoded = $null

    Push-Location $stage4uRoot
    try {
        & $stage4uPython -I -B ml_v4/evidence/stage4u_continue/live_checks.py preflight
        if ($LASTEXITCODE -ne 0) { throw 'Read-only test database preflight failed. No installer ran.' }

        & $stage4uPython -I -B ml_v4/evidence/stage4u/install_schema.py
        if ($LASTEXITCODE -ne 0) { throw 'Schema installer failed. Inspect the disposable database before any retry.' }

        & $stage4uPython -I -B ml_v4/test_binding/v1.py prepare
        if ($LASTEXITCODE -ne 0) { throw 'Test observation authority preparation failed. No fixture may be submitted.' }

        & $stage4uPython -I -B ml_v4/test_binding/v1.py check
        if ($LASTEXITCODE -ne 0) { throw 'Test authority check failed.' }

        & $stage4uPython -I -B ml_v4/evidence/stage4u_continue/live_checks.py verify
        if ($LASTEXITCODE -ne 0) { throw 'Final live isolation/history verification failed.' }

        Write-Output 'Stage4U isolated MySQL verification completed. No financial fixtures were submitted.'
    } finally {
        Pop-Location
    }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($stage4uPtr)
    Remove-Item Env:V4_STAGE4T_TEST_DB_URL -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4T_EXPECTED_SERVER_UUID -ErrorAction SilentlyContinue
    $stage4uPlain = $null
    $stage4uEncoded = $null
    $stage4uSecret = $null
}
