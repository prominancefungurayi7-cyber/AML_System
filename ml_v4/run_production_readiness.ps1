# Read-only production prerequisite inspection. Never enables V4 or runs DDL.
param(
    [Parameter(Mandatory=$true)][string]$HostName,
    [Parameter(Mandatory=$true)][string]$UserName,
    [Parameter(Mandatory=$true)][string]$Principal,
    [Parameter(Mandatory=$true)][string]$ServerUuid,
    [Parameter(Mandatory=$true)][string]$SocketOrigins,
    [Parameter(Mandatory=$true)][ValidateSet('On','Off')][string]$RuleEngine
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $root '.venv\Scripts\python.exe'
$infer = Join-Path $root 'ml_v4\.venv_inference_stage3\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python) -or -not (Test-Path -LiteralPath $infer)) {
    throw 'Approved application or inference Python runtime unavailable.'
}
if ($env:DATABASE_URL -or $env:MYSQL_URL -or $env:V4_STAGE4T_TEST_DB_URL -or
    $env:V4_READINESS_HOST -or $env:V4_READINESS_PASSWORD -or
    $env:SOCKETIO_ALLOWED_ORIGINS -or $env:AML_RULE_ENGINE_ENABLED -or
    $env:AML_PRIMARY_MODEL -eq 'V4') {
    throw 'Conflicting database binding or V4 activation detected.'
}
if ($HostName -notmatch '^[A-Za-z0-9.-]+$' -or $UserName -notmatch '^[A-Za-z0-9_]+$' -or
    $Principal -notmatch '^[A-Za-z0-9_]+@[A-Za-z0-9_.%:-]+$' -or
    $ServerUuid -notmatch '^[0-9a-f-]{36}$') { throw 'Invalid expected production identity.' }
$secret = Read-Host 'Password for the explicitly identified aml runtime account (read-only queries)' -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try {
    $env:V4_READINESS_HOST = $HostName
    $env:V4_READINESS_USER = $UserName
    $env:V4_READINESS_PRINCIPAL = $Principal
    $env:V4_READINESS_UUID = $ServerUuid
    $env:V4_READINESS_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    $env:AML_RULE_ENGINE_ENABLED = $RuleEngine.ToUpperInvariant()
    $env:SOCKETIO_ALLOWED_ORIGINS = $SocketOrigins
    Push-Location $root
    try {
        & $infer -I -B ml_v4/production_runtime_check.py
        if ($LASTEXITCODE -ne 0) { throw 'Pinned frozen inference runtime failed.' }
        & $python -B -m ml_v4.production_readiness
        if ($LASTEXITCODE -ne 0) { throw 'Production read-only readiness failed.' }
    } finally { Pop-Location }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    foreach ($name in @('V4_READINESS_HOST','V4_READINESS_USER','V4_READINESS_PRINCIPAL',
                        'V4_READINESS_UUID','V4_READINESS_PASSWORD','AML_RULE_ENGINE_ENABLED',
                        'SOCKETIO_ALLOWED_ORIGINS')) {
        Remove-Item "Env:$name" -ErrorAction SilentlyContinue
    }
    $secret = $null
}
