# Existing-admin trigger-only repair for local aml. Run only after approval.
param([switch]$Apply)
$ErrorActionPreference = 'Stop'
if (-not $Apply) { throw 'Explicit -Apply required.' }
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Local application Python unavailable.' }
foreach ($name in @('DATABASE_URL','MYSQL_URL','V4_STAGE4T_TEST_DB_URL',
                    'V4_STAGE4SK_RECOVERY_DB_URL','LOCAL_AML_ADMIN_PASSWORD',
                    'LOCAL_AML_TRIGGER_REPAIR_APPROVED')) {
    if ([Environment]::GetEnvironmentVariable($name)) { throw "Conflicting environment variable: $name" }
}
$adminUser = Read-Host 'Existing SUPER-capable MySQL administrator account name'
if ($adminUser -notmatch '^[A-Za-z0-9_]{1,32}$') { throw 'Invalid administrator account name.' }
$secret = Read-Host "Password for existing MySQL administrator $adminUser" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try {
    $env:LOCAL_AML_ADMIN_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    $env:LOCAL_AML_TRIGGER_REPAIR_APPROVED = 'YES'
    Push-Location $root
    try {
        & $python -B -m ml_v4.local_aml_trigger_repair --admin-user $adminUser --apply
        if ($LASTEXITCODE -ne 0) {
            throw 'Trigger DDL may have partially committed. Inspect read-only; do not rerun blindly.'
        }
    } finally { Pop-Location }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    Remove-Item Env:LOCAL_AML_ADMIN_PASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:LOCAL_AML_TRIGGER_REPAIR_APPROVED -ErrorAction SilentlyContinue
    $secret = $null
}
