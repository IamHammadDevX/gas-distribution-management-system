param(
    [string]$PgHost = "127.0.0.1",
    [int]$PgPort = 55432,
    [string]$PgDatabase = "rajput_gas",
    [string]$PgUser = "rajput_gas_app",
    [string]$PgPassword = "ChangeMe_RajputGas_2026!",
    [string]$AppTimezone = "Asia/Karachi"
)

$ErrorActionPreference = "Stop"

$python = "f:/gas-distribution-management-system/venv/Scripts/python.exe"
if (-not (Test-Path $python)) {
    throw "Python environment not found at $python"
}

$env:PGHOST = $PgHost
$env:PGPORT = "$PgPort"
$env:PGDATABASE = $PgDatabase
$env:PGUSER = $PgUser
$env:PGPASSWORD = $PgPassword
$env:APP_TIMEZONE = $AppTimezone

& $python -c "from src.database_module import DatabaseManager; db=DatabaseManager(); db.close(); print('PostgreSQL connection OK and schema initialized.')" | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw "Database preflight failed. Verify PostgreSQL server is running and credentials are correct."
}

& $python main.py
