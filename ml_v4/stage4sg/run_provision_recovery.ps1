# Stage4S-L prepared admin launcher. Do not use -Apply without separate approval.
param([string]$AdminUser = 'root', [switch]$Apply)
$ErrorActionPreference = 'Stop'
if (-not $Apply) { throw 'Explicit -Apply required; no administrator SQL executed.' }
if ($AdminUser -notmatch '^[A-Za-z0-9_]{1,32}$' -or $AdminUser -eq 'v4_stage4sk_restore') {
    throw 'Invalid administrator user.'
}
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$python = Join-Path $root 'ml_v4\.venv_inference_stage3\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Isolated Python runtime unavailable.' }
if ($env:DATABASE_URL -or $env:MYSQL_URL -or $env:V4_STAGE4T_TEST_DB_URL -or
    $env:V4_STAGE4SK_RECOVERY_DB_URL -or $env:V4_STAGE4SL_ADMIN_PASSWORD -or
    $env:V4_STAGE4SL_RECOVERY_PASSWORD) {
    throw 'Unset existing database credential and URL variables first.'
}
if ($env:V4_SHADOW_ENABLED -eq 'ON') { throw 'V4 shadow mode must remain OFF.' }
$originalSecret = Read-Host 'Restricted password for original disposable read-only checks' -AsSecureString
$originalPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($originalSecret)
$adminPtr = [IntPtr]::Zero
$recoveryPtr = [IntPtr]::Zero
try {
    Push-Location $root
    try {
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($originalPtr)
        $encoded = [Uri]::EscapeDataString($plain)
        $env:V4_STAGE4T_TEST_DB_URL = "mysql://v4_stage4t_runner:$encoded@127.0.0.1:3306/v4_stage4s_disposable"
        $env:V4_STAGE4T_EXPECTED_SERVER_UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
        $plain = $null; $encoded = $null
        $before = & $python -B -m ml_v4.stage4sg.preflight
        if ($LASTEXITCODE -ne 0) { throw 'Original disposable preflight failed before admin SQL.' }
        $beforeObject = ($before | Out-String | ConvertFrom-Json)
        if ($beforeObject.status -ne 'PASS') { throw 'Original disposable preflight status mismatch.' }
        Remove-Item Env:V4_STAGE4T_TEST_DB_URL -ErrorAction SilentlyContinue
        Remove-Item Env:V4_STAGE4T_EXPECTED_SERVER_UUID -ErrorAction SilentlyContinue

        $adminSecret = Read-Host "Administrator password for $AdminUser on pinned local MySQL" -AsSecureString
        $recoverySecret = Read-Host 'New password for v4_stage4sk_restore' -AsSecureString
        $adminPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($adminSecret)
        $recoveryPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($recoverySecret)
        $env:V4_STAGE4SL_ADMIN_USER = $AdminUser
        $env:V4_STAGE4SL_EXPECTED_SERVER_UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
        $env:V4_STAGE4SL_ADMIN_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($adminPtr)
        $env:V4_STAGE4SL_RECOVERY_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($recoveryPtr)
        try {
            $created = & $python -B -m ml_v4.stage4sg.provision_recovery --apply
            if ($LASTEXITCODE -ne 0) { throw 'Admin provisioning failed; inspect partial target before retry.' }
        } finally {
            Remove-Item Env:V4_STAGE4SL_ADMIN_PASSWORD -ErrorAction SilentlyContinue
            Remove-Item Env:V4_STAGE4SL_RECOVERY_PASSWORD -ErrorAction SilentlyContinue
        }
        $createdObject = ($created | Out-String | ConvertFrom-Json)
        if ($createdObject.status -ne 'PROVISIONED_EMPTY_RECOVERY') { throw 'Provision result mismatch.' }

        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($recoveryPtr)
        $encoded = [Uri]::EscapeDataString($plain)
        $env:V4_STAGE4SK_RECOVERY_DB_URL = "mysql://v4_stage4sk_restore:$encoded@127.0.0.1:3306/v4_stage4sk_recovery"
        $env:V4_STAGE4SK_EXPECTED_SERVER_UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
        $plain = $null; $encoded = $null
        $target = & $python -B -m ml_v4.stage4sg.recovery_guard before --exact-grants
        if ($LASTEXITCODE -ne 0) { throw 'Recovery account identity/grants/empty-state check failed.' }
        $targetObject = ($target | Out-String | ConvertFrom-Json)
        if ($targetObject.status -ne 'EMPTY_RECOVERY_VERIFIED') { throw 'Recovery database is not empty.' }
        Remove-Item Env:V4_STAGE4SK_RECOVERY_DB_URL -ErrorAction SilentlyContinue
        Remove-Item Env:V4_STAGE4SK_EXPECTED_SERVER_UUID -ErrorAction SilentlyContinue

        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($originalPtr)
        $encoded = [Uri]::EscapeDataString($plain)
        $env:V4_STAGE4T_TEST_DB_URL = "mysql://v4_stage4t_runner:$encoded@127.0.0.1:3306/v4_stage4s_disposable"
        $env:V4_STAGE4T_EXPECTED_SERVER_UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
        $plain = $null; $encoded = $null
        $after = & $python -B -m ml_v4.stage4sg.preflight
        if ($LASTEXITCODE -ne 0) { throw 'Original disposable post-provision preflight failed.' }
        $afterObject = ($after | Out-String | ConvertFrom-Json)
        if (($afterObject.existing_row_sha256 | ConvertTo-Json -Compress) -ne
            ($beforeObject.existing_row_sha256 | ConvertTo-Json -Compress)) {
            throw 'Original disposable row digests changed during provisioning.'
        }
        [pscustomobject]@{
            status = 'RECOVERY_PROVISIONING_VERIFIED'
            database = 'v4_stage4sk_recovery'
            account = 'v4_stage4sk_restore@127.0.0.1'
            server_uuid = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
            recovery_table_count = 0
            original_preflight_before_after = 'PASS'
            original_row_digests_unchanged = $true
        } | ConvertTo-Json
    } finally { Pop-Location }
} finally {
    Remove-Item Env:V4_STAGE4T_TEST_DB_URL -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4T_EXPECTED_SERVER_UUID -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4SK_RECOVERY_DB_URL -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4SK_EXPECTED_SERVER_UUID -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4SL_ADMIN_USER -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4SL_EXPECTED_SERVER_UUID -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4SL_ADMIN_PASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:V4_STAGE4SL_RECOVERY_PASSWORD -ErrorAction SilentlyContinue
    $plain = $null; $encoded = $null
    if ($adminPtr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($adminPtr) }
    if ($recoveryPtr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($recoveryPtr) }
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($originalPtr)
    $originalSecret = $null; $adminSecret = $null; $recoverySecret = $null
}
