$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$redisExe = Join-Path $env:ProgramFiles 'Memurai\memurai.exe'
$stateDir = Join-Path $projectRoot 'data\local-redis'
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
if (-not (Test-Path -LiteralPath $redisExe)) {
    throw 'Install Memurai Developer first; approve its Windows administrator prompt.'
}
$redisConfig = Join-Path $stateDir 'memurai.conf'
if (-not (Test-Path -LiteralPath $redisConfig)) {
    @'
bind 127.0.0.1
protected-mode yes
port 6379
maxmemory 128mb
maxmemory-policy noeviction
save ""
appendonly no
logfile "memurai.log"
'@ | Set-Content -LiteralPath $redisConfig -Encoding ascii
}
# Redis is transient event infrastructure; financial records remain in MySQL.
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
& $python -c "import redis,sys; r=redis.Redis(host='127.0.0.1',port=6379,socket_connect_timeout=1); exec('try:\n r.ping()\nexcept Exception:\n sys.exit(1)')" 2>$null
if ($LASTEXITCODE -ne 0) {
    Start-Process -FilePath $redisExe -ArgumentList ('"' + $redisConfig + '"') -WorkingDirectory $stateDir -WindowStyle Hidden | Out-Null
    $ready = $false
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        Start-Sleep -Milliseconds 250
        & $python -c "import redis,sys; r=redis.Redis(host='127.0.0.1',port=6379,socket_connect_timeout=1); exec('try:\n r.ping()\nexcept Exception:\n sys.exit(1)')" 2>$null
        if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    }
    if (-not $ready) { throw 'Redis did not start; inspect data/local-redis/memurai.log.' }
}
$env:AML_PRIMARY_MODEL = 'V4'
$env:AML_RULE_ENGINE_ENABLED = 'ON'
$env:SOCKETIO_ALLOWED_ORIGINS = 'http://127.0.0.1:5000'
$env:REDIS_URL = 'redis://127.0.0.1:6379/0'
try { $existing = Invoke-RestMethod -Uri 'http://127.0.0.1:5000/health' -TimeoutSec 3 } catch { $existing = $null }
if ($existing) {
    if ($existing.primary_model -ne 'V4' -or -not $existing.rules_enabled -or -not $existing.realtime.redis_connected) {
        throw 'An existing Flask instance needs restarting with the current configuration. No duplicate instance was started.'
    }
    Write-Output 'V4, independent rules and Redis are already running at http://127.0.0.1:5000.'
    exit 0
}
Start-Process -FilePath $python -ArgumentList 'server.py' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $stateDir 'flask.stdout.log') -RedirectStandardError (Join-Path $stateDir 'flask.stderr.log') | Out-Null
$appReady = $false
for ($attempt = 0; $attempt -lt 45; $attempt++) {
    Start-Sleep -Milliseconds 1000
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:5000/health' -TimeoutSec 2
        if ($health.primary_model -eq 'V4' -and $health.rules_enabled -and $health.realtime.redis_connected) { $appReady = $true; break }
    } catch { }
}
if (-not $appReady) { throw 'Flask readiness did not pass; inspect data/local-redis/flask.stderr.log.' }
Write-Output 'V4, independent rules and Redis are running at http://127.0.0.1:5000.'
