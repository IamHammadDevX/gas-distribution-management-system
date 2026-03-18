param(
    [string]$DataDir = "f:/gas-distribution-management-system/.postgres/data",
    [string]$PgBinDir = "f:/gas-distribution-management-system/.postgres/pgsql/pgsql/bin",
    [string]$PgShareDir = "f:/gas-distribution-management-system/.postgres/pgsql/pgsql/share",
    [string]$PgHost = "127.0.0.1",
    [int]$Port = 55432,
    [string]$SuperUser = "postgres",
    [string]$SuperPassword = "ChangeMe_PostgresAdmin_2026!",
    [string]$AppDb = "rajput_gas",
    [string]$AppUser = "rajput_gas_app",
    [string]$AppPassword = "ChangeMe_RajputGas_2026!"
)

$ErrorActionPreference = "Stop"

function Get-Bin([string]$name) {
    $path = Join-Path $PgBinDir $name
    if (-not (Test-Path $path)) {
        throw "Missing PostgreSQL binary: $path"
    }
    return $path
}

function Set-ConfigValue([string]$FilePath, [string]$Key, [string]$ValueLiteral) {
    if (-not (Test-Path $FilePath)) {
        New-Item -Path $FilePath -ItemType File -Force | Out-Null
    }

    $content = Get-Content -Path $FilePath -Raw
    $pattern = "(?m)^\s*#?\s*" + [regex]::Escape($Key) + "\s*=.*$"
    $line = "$Key = $ValueLiteral"

    if ([regex]::IsMatch($content, $pattern)) {
        $newContent = [regex]::Replace($content, $pattern, $line)
    }
    else {
        if ($content -and -not $content.EndsWith("`n")) {
            $content += "`r`n"
        }
        $newContent = $content + $line + "`r`n"
    }

    Set-Content -Path $FilePath -Value $newContent -Encoding UTF8
}

$initdb = Get-Bin "initdb.exe"
$pgCtl = Get-Bin "pg_ctl.exe"
$pgIsReady = Get-Bin "pg_isready.exe"
$psql = Get-Bin "psql.exe"

if (-not (Test-Path $PgShareDir)) {
    throw "PostgreSQL sharedir not found at '$PgShareDir'. Install a full PostgreSQL server package (including share/postgres.bki) and rerun this script with -PgShareDir set correctly."
}

if (-not (Test-Path (Join-Path $PgShareDir "postgres.bki"))) {
    throw "Missing '$PgShareDir/postgres.bki'. Your PostgreSQL installation appears incomplete. Reinstall PostgreSQL server tools and rerun."
}

if (-not (Test-Path $DataDir)) {
    New-Item -Path $DataDir -ItemType Directory -Force | Out-Null
}

$pgVersionFile = Join-Path $DataDir "PG_VERSION"
if (-not (Test-Path $pgVersionFile)) {
    # If a prior failed bootstrap left files behind, clear them before initdb.
    $existing = Get-ChildItem -Path $DataDir -Force -ErrorAction SilentlyContinue
    if ($existing) {
        Remove-Item -Path (Join-Path $DataDir "*") -Recurse -Force -ErrorAction SilentlyContinue
    }

    Write-Host "Initializing PostgreSQL cluster at $DataDir ..."

    $pwFile = Join-Path $env:TEMP "pg_super_pw_$([guid]::NewGuid().ToString('N')).txt"
    Set-Content -Path $pwFile -Value $SuperPassword -NoNewline -Encoding UTF8

    try {
        & $initdb -D $DataDir -U $SuperUser -A scram-sha-256 --pwfile $pwFile -L $PgShareDir | Out-Host
        if ($LASTEXITCODE -ne 0) {
            throw "initdb failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        if (Test-Path $pwFile) { Remove-Item -Path $pwFile -Force }
    }
}
else {
    Write-Host "PostgreSQL cluster already initialized at $DataDir"
}

$postgresqlConf = Join-Path $DataDir "postgresql.conf"
$pgHbaConf = Join-Path $DataDir "pg_hba.conf"

Set-ConfigValue -FilePath $postgresqlConf -Key "listen_addresses" -ValueLiteral "'$PgHost'"
Set-ConfigValue -FilePath $postgresqlConf -Key "port" -ValueLiteral "$Port"
Set-ConfigValue -FilePath $postgresqlConf -Key "password_encryption" -ValueLiteral "'scram-sha-256'"

# Durability-focused settings
Set-ConfigValue -FilePath $postgresqlConf -Key "wal_level" -ValueLiteral "'replica'"
Set-ConfigValue -FilePath $postgresqlConf -Key "fsync" -ValueLiteral "on"
Set-ConfigValue -FilePath $postgresqlConf -Key "synchronous_commit" -ValueLiteral "on"
Set-ConfigValue -FilePath $postgresqlConf -Key "full_page_writes" -ValueLiteral "on"

if (-not (Test-Path $pgHbaConf)) {
    New-Item -Path $pgHbaConf -ItemType File -Force | Out-Null
}
$hba = @(
    "# TYPE  DATABASE        USER            ADDRESS                 METHOD",
    "local   all             all                                     scram-sha-256",
    "host    all             all             127.0.0.1/32            scram-sha-256"
)
Set-Content -Path $pgHbaConf -Value ($hba -join "`r`n") -Encoding UTF8

$readyOutput = & $pgIsReady -h $PgHost -p $Port 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Starting PostgreSQL on ${PgHost}:$Port ..."
    $logFile = Join-Path $DataDir "postgresql.log"
    & $pgCtl -D $DataDir -l $logFile start | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "pg_ctl start failed with exit code $LASTEXITCODE"
    }

    Start-Sleep -Seconds 2
    $readyOutput = & $pgIsReady -h $PgHost -p $Port 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL did not start successfully. pg_isready output: $readyOutput"
    }
}

$env:PGPASSWORD = $SuperPassword

$escapedAppPassword = $AppPassword.Replace("'", "''")
$escapedAppUser = $AppUser.Replace('"', '""')
$escapedAppDb = $AppDb.Replace('"', '""')

$roleExists = (& $psql -h $PgHost -p $Port -U $SuperUser -d postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname = '$AppUser';").Trim()
if ($roleExists -ne "1") {
    & $psql -h $PgHost -p $Port -U $SuperUser -d postgres -v ON_ERROR_STOP=1 -c "CREATE ROLE \"$escapedAppUser\" LOGIN PASSWORD '$escapedAppPassword';" | Out-Host
}

$dbExists = (& $psql -h $PgHost -p $Port -U $SuperUser -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$AppDb';").Trim()
if ($dbExists -ne "1") {
    & $psql -h $PgHost -p $Port -U $SuperUser -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"$escapedAppDb\" OWNER \"$escapedAppUser\";" | Out-Host
}

& $psql -h $PgHost -p $Port -U $SuperUser -d $AppDb -v ON_ERROR_STOP=1 -c "GRANT CONNECT ON DATABASE \"$escapedAppDb\" TO \"$escapedAppUser\";" | Out-Null
& $psql -h $PgHost -p $Port -U $SuperUser -d $AppDb -v ON_ERROR_STOP=1 -c "GRANT USAGE, CREATE ON SCHEMA public TO \"$escapedAppUser\";" | Out-Null
& $psql -h $PgHost -p $Port -U $SuperUser -d $AppDb -v ON_ERROR_STOP=1 -c "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"$escapedAppUser\";" | Out-Null
& $psql -h $PgHost -p $Port -U $SuperUser -d $AppDb -v ON_ERROR_STOP=1 -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO \"$escapedAppUser\";" | Out-Null

Write-Host ""
Write-Host "PostgreSQL setup complete. Use these environment variables for the app:"
Write-Host "  `$env:PGHOST='$PgHost'"
Write-Host "  `$env:PGPORT='$Port'"
Write-Host "  `$env:PGDATABASE='$AppDb'"
Write-Host "  `$env:PGUSER='$AppUser'"
Write-Host "  `$env:PGPASSWORD='$AppPassword'"
Write-Host "  `$env:APP_TIMEZONE='Asia/Karachi'"
