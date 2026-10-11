# Administrator DDL on the pinned disposable schema only; no global SET/GRANT.
param(
    [Parameter(Mandatory=$true)][string]$AdminUser,
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
if (-not $Apply) { throw 'Explicit -Apply required. No database write attempted.' }
if ($AdminUser -notmatch '^[A-Za-z0-9_]{1,32}$') { throw 'Invalid administrator account name.' }
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$app = Join-Path $root '.venv\Scripts\python.exe'
$infer = Join-Path $root 'ml_v4\.venv_inference_stage3\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $app) -or -not (Test-Path -LiteralPath $infer)) {
    throw 'Approved isolated Python runtimes unavailable.'
}
if ($env:DATABASE_URL -or $env:MYSQL_URL -or $env:V4_STAGE4T_TEST_DB_URL -or
    $env:V4_STAGE4SK_RECOVERY_DB_URL -or $env:STAGE5C_SCHEMA_APPLY -or
    $env:STAGE5C_TRIGGER_REPAIR_APPLY -or $env:STAGE5C_ADMIN_TRIGGER_APPLY -or
    $env:STAGE5C_ADMIN_PASSWORD -or $env:STAGE5C_ADMIN_USER) {
    throw 'Unset inherited database or schema variables.'
}
$testSecret = Read-Host 'Restricted v4_stage4t_runner password for disposable preflight' -AsSecureString
$adminSecret = Read-Host "Password for existing MySQL administrator $AdminUser" -AsSecureString
$testPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($testSecret)
$adminPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($adminSecret)
try {
    $testPlain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($testPtr)
    $adminPlain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($adminPtr)
    $encoded = [Uri]::EscapeDataString($testPlain)
    $env:V4_STAGE4T_TEST_DB_URL = "mysql://v4_stage4t_runner:$encoded@127.0.0.1:3306/v4_stage4s_disposable"
    $env:V4_STAGE4T_EXPECTED_SERVER_UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
    $env:STAGE5C_ADMIN_USER = $AdminUser
    $env:STAGE5C_ADMIN_PASSWORD = $adminPlain
    $env:STAGE5C_ADMIN_TRIGGER_APPLY = 'YES'
    $testPlain = $null
    $adminPlain = $null
    $encoded = $null
    Push-Location $root
    try {
        & $infer -I -B ml_v4/test_binding/v1.py check
        if ($LASTEXITCODE -ne 0) { throw 'Disposable identity/authority check failed.' }
        & $app -B -m ml_v4.stage5c.admin_repair_retry_triggers --apply
        if ($LASTEXITCODE -ne 0) {
            throw 'Trigger DDL may have partially committed. Inspect read-only; do not retry.'
        }
    } finally { Pop-Location }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($testPtr)
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($adminPtr)
    foreach ($name in @('V4_STAGE4T_TEST_DB_URL','V4_STAGE4T_EXPECTED_SERVER_UUID',
                        'STAGE5C_ADMIN_USER','STAGE5C_ADMIN_PASSWORD',
                        'STAGE5C_ADMIN_TRIGGER_APPLY')) {
        Remove-Item "Env:$name" -ErrorAction SilentlyContinue
    }
    $testPlain = $null
    $adminPlain = $null
    $encoded = $null
    $testSecret = $null
    $adminSecret = $null
}
