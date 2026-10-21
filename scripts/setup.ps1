# Prepares a fresh clone for `docker compose up` on Windows (PowerShell).
#  - .env from .env.example (if missing)
#  - ./secrets/*.txt with random passwords (only missing ones)
#  - self-signed TLS certificate for the IDM gRPC server (certs/idm.crt, certs/idm.key)
# Usage (from the repository root):  powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    $jwt = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 48 | ForEach-Object { [char]$_ })
    (Get-Content ".env") -replace "^IDM_JWT_SECRET=.*", "IDM_JWT_SECRET=$jwt" | Set-Content ".env"
    Write-Host "created .env"
}

New-Item -ItemType Directory -Force -Path "secrets" | Out-Null
$names = "db_root_pass","db_user_pass","db_admin_pass","mongo_admin_pass","mongo_db_owner_pass","mongo_app_pass","idm_db_root_pass","idm_db_pass"
foreach ($n in $names) {
    $f = "secrets\$n.txt"
    if (-not (Test-Path $f)) {
        $pw = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 24 | ForEach-Object { [char]$_ })
        [IO.File]::WriteAllText((Join-Path $root $f), $pw)   # no trailing newline
        Write-Host "created $f"
    }
}

if (-not (Test-Path "certs\idm.crt") -or -not (Test-Path "certs\idm.key")) {
    $sslArgs = @("req","-x509","-nodes","-newkey","rsa:2048","-days","365",
              "-keyout","/certs/idm.key","-out","/certs/idm.crt",
              "-config","/certs/idm_openssl.cnf","-extensions","req_ext")
    # openssl runs in a throw-away container, so nothing needs to be installed on Windows
    docker run --rm -v "${root}\certs:/certs" alpine/openssl @sslArgs
    Write-Host "created certs\idm.crt and certs\idm.key"
}

Write-Host "done. Next: docker compose up --build"
