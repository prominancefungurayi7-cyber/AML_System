# Stage4S-J: read-only disposable backup. Requires a local mysqldump utility.
param([string]$DumpPath)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$python = Join-Path $root 'ml_v4\.venv_inference_stage3\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Isolated Python runtime unavailable.' }
if ($env:DATABASE_URL -or $env:MYSQL_URL -or $env:V4_STAGE4T_TEST_DB_URL -or $env:MYSQL_PWD) {
    throw 'Unset database URL and MYSQL_PWD variables before backup.'
}
if ($env:V4_SHADOW_ENABLED -eq 'ON') { throw 'V4 shadow mode must remain OFF.' }
if ($DumpPath) {
    $dump = (Resolve-Path -LiteralPath $DumpPath).Path
    if ([IO.Path]::GetFileName($dump) -notin @('mysqldump.exe','mariadb-dump.exe')) {
        throw 'Dump utility must be mysqldump.exe or mariadb-dump.exe.'
    }
} else {
    $command = Get-Command mysqldump.exe,mariadb-dump.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $command) { throw 'Compatible mysqldump utility unavailable.' }
    $dump = $command.Source
}
$version = (& $dump --version | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or -not $version) { throw 'Dump utility version check failed.' }
if (-not $env:LOCALAPPDATA) { throw 'LOCALAPPDATA unavailable.' }
$backupRoot = Join-Path $env:LOCALAPPDATA 'AML-Stage4SJ-Backups'
if (-not (Test-Path -LiteralPath $backupRoot)) { New-Item -ItemType Directory -Path $backupRoot | Out-Null }
$backupRoot = (Resolve-Path -LiteralPath $backupRoot).Path
if ($backupRoot.StartsWith($root,[StringComparison]::OrdinalIgnoreCase)) { throw 'Backup directory is inside the repository.' }
$account = [Security.Principal.WindowsIdentity]::GetCurrent().Name
& icacls.exe $backupRoot /inheritance:r /grant:r "${account}:(OI)(CI)F" | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Unable to restrict backup directory ACL.' }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fffffff'
$backup = Join-Path $backupRoot "v4_stage4s_disposable-$stamp.sql"
[IO.File]::Open($backup,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None).Close()
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
        $preflight = & $python -B -m ml_v4.stage4sg.preflight
        if ($LASTEXITCODE -ne 0) { throw 'Disposable preflight failed; backup not started.' }
        $preflightObject = ($preflight | Out-String | ConvertFrom-Json)
        if ($preflightObject.status -ne 'PASS') { throw 'Disposable preflight did not pass.' }
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
        $env:MYSQL_PWD = $plain
        $plain = $null
        try {
            # --skip-extended-insert gives one INSERT per row for structural count verification.
            & $dump --host=127.0.0.1 --port=3306 --user=v4_stage4t_runner `
                --single-transaction --quick --skip-lock-tables --skip-extended-insert `
                --triggers --hex-blob --no-tablespaces --databases v4_stage4s_disposable `
                "--result-file=$backup" 2>$null
            if ($LASTEXITCODE -ne 0) { throw 'Dump utility failed; backup is not verified.' }
        } finally {
            Remove-Item Env:MYSQL_PWD -ErrorAction SilentlyContinue
        }
        $indexArgs = @()
        foreach ($name in @($preflightObject.transaction_indexes | Select-Object -ExpandProperty Key_name -Unique)) {
            $indexArgs += @('--expected-index', [string]$name)
        }
        $verified = & $python -B -m ml_v4.stage4sg.verify_backup $backup @indexArgs
        if ($LASTEXITCODE -ne 0) { throw 'Backup structural verification failed.' }
        $after = & $python -B -m ml_v4.stage4sg.preflight
        if ($LASTEXITCODE -ne 0) { throw 'Post-backup disposable preflight failed.' }
        $afterObject = ($after | Out-String | ConvertFrom-Json)
        if (($afterObject.existing_row_sha256 | ConvertTo-Json -Compress) -ne `
            ($preflightObject.existing_row_sha256 | ConvertTo-Json -Compress)) {
            throw 'Disposable row digests changed during backup.'
        }
        $result = ($verified | Out-String | ConvertFrom-Json)
        $result | Add-Member -NotePropertyName utility_version -NotePropertyValue $version
        $result | Add-Member -NotePropertyName preflight_before_after -NotePropertyValue 'PASS'
        $result | ConvertTo-Json -Depth 8
    } finally { Pop-Location }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    Remove-Item Env:MYSQL_PWD -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4T_TEST_DB_URL -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4T_EXPECTED_SERVER_UUID -ErrorAction SilentlyContinue
    $plain = $null
    $encoded = $null
    $secret = $null
}
