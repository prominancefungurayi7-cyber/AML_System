# Stage5A: prepared, disposable-only migration launcher. Never run automatically.
param([switch]$Apply)
$ErrorActionPreference = 'Stop'
if (-not $Apply) { throw 'Explicit -Apply required; migration was not run.' }
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$python = Join-Path $root 'ml_v4\.venv_inference_stage3\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Isolated Python runtime unavailable.' }
if ($env:DATABASE_URL -or $env:MYSQL_URL -or $env:V4_STAGE4T_TEST_DB_URL -or
    $env:V4_STAGE4SK_RECOVERY_DB_URL) {
    throw 'Unset existing database URLs before the disposable migration.'
}
if ($env:V4_SHADOW_ENABLED -eq 'ON') { throw 'Production V4 shadow mode must remain OFF.' }
if (-not $env:LOCALAPPDATA) { throw 'LOCALAPPDATA unavailable.' }
$backupRoot = (Resolve-Path -LiteralPath (Join-Path $env:LOCALAPPDATA 'AML-Stage4SJ-Backups')).Path
$backup = Join-Path $backupRoot 'v4_stage4s_disposable-20261009-225015-3681550.sql'
if (-not (Test-Path -LiteralPath $backup)) { throw 'Pinned disposable backup unavailable.' }
$expectedHash = 'b883ecb0fa7132106b5b1eeb91f26369e708e51ec54298b542251a9dd8e6c85c'
if ((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) {
    throw 'Pinned disposable backup SHA-256 mismatch.'
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
        $backupCheck = & $python -B -m ml_v4.stage4sg.verify_backup $backup
        if ($LASTEXITCODE -ne 0) { throw 'Pinned backup structural check failed.' }
        $backupInfo = ($backupCheck | Out-String | ConvertFrom-Json)
        if ($backupInfo.sha256 -ne $expectedHash -or $backupInfo.status -ne 'STRUCTURALLY_VERIFIED') {
            throw 'Pinned backup verification mismatch.'
        }
        $preflight = & $python -B -m ml_v4.stage4sg.preflight
        if ($LASTEXITCODE -ne 0) { throw 'Disposable preflight failed; migration not run.' }
        $preflightInfo = ($preflight | Out-String | ConvertFrom-Json)
        if ($preflightInfo.status -ne 'PASS' -or $preflightInfo.counts.transactions -ne 4) {
            throw 'Disposable preflight result mismatch.'
        }
        & $python -B -m ml_v4.stage4sg.mysql_migration --apply --expected-transactions 4
        if ($LASTEXITCODE -ne 0) {
            throw 'Migration failed. MySQL DDL may have committed; inspect read-only before any retry.'
        }
        Write-Output 'Disposable idempotency migration completed and its post-DDL checks passed.'
    } finally { Pop-Location }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    Remove-Item Env:V4_STAGE4T_TEST_DB_URL -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4T_EXPECTED_SERVER_UUID -ErrorAction SilentlyContinue
    $plain = $null
    $encoded = $null
    $secret = $null
}
