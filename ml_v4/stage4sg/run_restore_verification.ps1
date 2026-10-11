# Stage4S-K prepared runner. DO NOT INVOKE -Apply until separately approved.
param(
    [Parameter(Mandatory=$true)][string]$BackupPath,
    [string]$OriginalEvidencePath,
    [string]$MysqlPath,
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
if (-not $Apply) { throw 'Explicit -Apply required; preparation does not restore.' }
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$python = Join-Path $root 'ml_v4\.venv_inference_stage3\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Isolated Python runtime unavailable.' }
if ($env:DATABASE_URL -or $env:MYSQL_URL -or $env:V4_STAGE4T_TEST_DB_URL -or
    $env:V4_STAGE4SK_RECOVERY_DB_URL -or $env:MYSQL_PWD) {
    throw 'Unset existing database URL and password variables first.'
}
if ($env:V4_SHADOW_ENABLED -eq 'ON') { throw 'V4 shadow mode must remain OFF.' }
if (-not $env:LOCALAPPDATA) { throw 'LOCALAPPDATA unavailable.' }
$backupRoot = (Resolve-Path -LiteralPath (Join-Path $env:LOCALAPPDATA 'AML-Stage4SJ-Backups')).Path
$backup = (Resolve-Path -LiteralPath $BackupPath).Path
if (-not $backup.StartsWith($backupRoot + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetFileName($backup) -ne 'v4_stage4s_disposable-20261009-225015-3681550.sql') {
    throw 'Backup path is outside the pinned restricted directory or has wrong name.'
}
if ($backup.StartsWith($root,[StringComparison]::OrdinalIgnoreCase)) { throw 'Backup must be outside Git.' }
if ($MysqlPath) {
    $mysql = (Resolve-Path -LiteralPath $MysqlPath).Path
    if ([IO.Path]::GetFileName($mysql) -notin @('mysql.exe','mariadb.exe')) {
        throw 'Restore utility must be mysql.exe or mariadb.exe.'
    }
} else {
    $command = Get-Command mysql.exe,mariadb.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $command) { throw 'Compatible MySQL restore utility unavailable.' }
    $mysql = $command.Source
}
$prepared = Join-Path $backupRoot ('v4_stage4sk_recovery-' + [guid]::NewGuid().ToString('N') + '.sql')
$stdout = Join-Path $backupRoot ('restore-' + [guid]::NewGuid().ToString('N') + '.stdout')
$stderr = Join-Path $backupRoot ('restore-' + [guid]::NewGuid().ToString('N') + '.stderr')
$secret = Read-Host 'Password for v4_stage4sk_restore on recovery database only' -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try {
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    $encoded = [Uri]::EscapeDataString($plain)
    $env:V4_STAGE4SK_RECOVERY_DB_URL = "mysql://v4_stage4sk_restore:$encoded@127.0.0.1:3306/v4_stage4sk_recovery"
    $env:V4_STAGE4SK_EXPECTED_SERVER_UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
    $plain = $null
    $encoded = $null
    Push-Location $root
    try {
        $backupCheck = & $python -B -m ml_v4.stage4sg.verify_backup $backup
        if ($LASTEXITCODE -ne 0) { throw 'Pinned backup structural check failed.' }
        $backupInfo = ($backupCheck | Out-String | ConvertFrom-Json)
        if ($backupInfo.sha256 -ne 'b883ecb0fa7132106b5b1eeb91f26369e708e51ec54298b542251a9dd8e6c85c') {
            throw 'Pinned backup SHA-256 mismatch.'
        }
        $before = & $python -B -m ml_v4.stage4sg.recovery_guard before
        if ($LASTEXITCODE -ne 0) { throw 'Recovery target identity/grants/empty-state check failed.' }
        $beforeInfo = ($before | Out-String | ConvertFrom-Json)
        if ($beforeInfo.status -ne 'EMPTY_RECOVERY_VERIFIED') { throw 'Recovery database is not empty.' }
        $rewrite = & $python -B -m ml_v4.stage4sg.restore_sql $backup $prepared
        if ($LASTEXITCODE -ne 0) { throw 'Safe SQL retargeting failed.' }
        $rewriteInfo = ($rewrite | Out-String | ConvertFrom-Json)
        if ($rewriteInfo.database -ne 'v4_stage4sk_recovery') { throw 'Prepared SQL target mismatch.' }
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
        $env:MYSQL_PWD = $plain
        $plain = $null
        try {
            $arguments = @('--host=127.0.0.1','--port=3306','--user=v4_stage4sk_restore',
                           '--database=v4_stage4sk_recovery','--default-character-set=utf8mb4')
            $process = Start-Process -FilePath $mysql -ArgumentList $arguments -WindowStyle Hidden `
                -RedirectStandardInput $prepared -RedirectStandardOutput $stdout `
                -RedirectStandardError $stderr -PassThru -Wait
            if ($process.ExitCode -ne 0) {
                throw 'Restore utility failed; recovery schema may be partially populated. No automatic retry.'
            }
        } finally {
            Remove-Item Env:MYSQL_PWD -ErrorAction SilentlyContinue
        }
        $indexArgs = @()
        foreach ($name in @($backupInfo.dump_transaction_indexes)) {
            $indexArgs += @('--expected-index', [string]$name)
        }
        foreach ($name in @($backupInfo.table_definitions)) {
            $indexArgs += @('--expected-table', [string]$name)
        }
        $evidenceArgs = @()
        if ($OriginalEvidencePath) { $evidenceArgs = @('--original-evidence', $OriginalEvidencePath) }
        $after = & $python -B -m ml_v4.stage4sg.recovery_guard after @indexArgs @evidenceArgs
        if ($LASTEXITCODE -ne 0) { throw 'Restored recovery database failed verification.' }
        $afterInfo = ($after | Out-String | ConvertFrom-Json)
        if ($afterInfo.status -ne 'RESTORED_ROWS_VERIFIED') { throw 'Post-restore status mismatch.' }
        [pscustomobject]@{
            status = 'RESTORE_REHEARSAL_VERIFIED'
            database = 'v4_stage4sk_recovery'
            backup_sha256 = $backupInfo.sha256
            prepared_sql_sha256 = $rewriteInfo.prepared_sha256
            restored_counts = $afterInfo.counts
            capture_triggers = $afterInfo.capture_triggers
            matched_original_preflight = $afterInfo.matched_original_preflight
        } | ConvertTo-Json -Depth 8
    } finally { Pop-Location }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    Remove-Item Env:MYSQL_PWD -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4SK_RECOVERY_DB_URL -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4SK_EXPECTED_SERVER_UUID -ErrorAction SilentlyContinue
    $plain = $null
    $encoded = $null
    $secret = $null
    if (Test-Path -LiteralPath $prepared) { Remove-Item -LiteralPath $prepared -Force }
}
