<#
.SYNOPSIS
  ShopAgent launcher — checks Docker, starts infra if needed, then launches Chainlit.
.PARAMETER Day
  Which day's Chainlit app to launch (3 or 4). Default: 3
.PARAMETER SkipDocker
  Skip Docker health check and start (useful for cloud mode)
.EXAMPLE
  .\start-shopagent.ps1          # Day 3, auto-start Docker
  .\start-shopagent.ps1 -Day 4   # Day 4, auto-start Docker
  .\start-shopagent.ps1 -SkipDocker  # Skip Docker check (cloud mode)
#>

param(
    [int]$Day = 3,
    [switch]$SkipDocker
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

# ── Load .env ──────────────────────────────────────────────────────
$envFile = Join-Path $ProjectRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and !$line.StartsWith("#") -and $line -match "=") {
            $parts = $line -split "=", 2
            $key = $parts[0].Trim()
            $val = $parts[1].Trim().Trim('"')
            [Environment]::SetEnvironmentVariable($key, $val, "Process")
        }
    }
}

$envMode = [Environment]::GetEnvironmentVariable("ENVIRONMENT", "Process")
if (-not $envMode) { $envMode = "local" }

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ShopAgent Launcher" -ForegroundColor Cyan
Write-Host "  Day: $Day  |  Environment: $envMode" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ── Docker check (skip in cloud mode or with -SkipDocker) ─────────
if ($envMode -eq "cloud" -or $SkipDocker) {
    Write-Host "[SKIP] Docker check bypassed (cloud mode or -SkipDocker)" -ForegroundColor Yellow
} else {
    # Check Docker is running
    Write-Host "[CHECK] Docker daemon..." -ForegroundColor White -NoNewline
    try {
        $null = docker info 2>&1
        Write-Host " RUNNING" -ForegroundColor Green
    } catch {
        Write-Host " NOT RUNNING" -ForegroundColor Red
        Write-Host "[START] Starting Docker Desktop..." -ForegroundColor Yellow
        $dockerPath = Get-Command "Docker Desktop" -ErrorAction SilentlyContinue
        if (-not $dockerPath) {
            $candidates = @(
                "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
                "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
                "$env:LOCALAPPDATA\Docker\Docker\Docker Desktop.exe"
            )
            foreach ($c in $candidates) {
                if (Test-Path $c) { $dockerPath = $c; break }
            }
        }
        if ($dockerPath) {
            Start-Process $dockerPath
            Write-Host "[WAIT] Waiting for Docker daemon to start..." -ForegroundColor Yellow
            $retries = 0
            while ($retries -lt 30) {
                Start-Sleep -Seconds 5
                try { $null = docker info 2>&1; break } catch { $retries++ }
                Write-Host "  ... still waiting ($retries/30)" -ForegroundColor DarkGray
            }
            if ($retries -ge 30) {
                Write-Host "[FAIL] Docker daemon did not start in 150s. Aborting." -ForegroundColor Red
                exit 1
            }
            Write-Host "  Docker daemon is UP" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] Docker Desktop not found. Install Docker or use -SkipDocker." -ForegroundColor Red
            exit 1
        }
    }

    # Check docker-compose services
    $composeDir = Join-Path $ProjectRoot "gen"
    Write-Host "[CHECK] Docker services (postgres, qdrant)..." -ForegroundColor White

    $composeStatus = docker compose -f "$composeDir\docker-compose.yml" ps --format json 2>&1
    $postgresUp = $composeStatus | Select-String "postgres" -Quiet
    $qdrantUp = $composeStatus | Select-String "qdrant" -Quiet

    if (-not $postgresUp -or -not $qdrantUp) {
        Write-Host "[START] Starting Docker services..." -ForegroundColor Yellow
        Push-Location $composeDir
        docker compose up -d 2>&1 | Write-Host
        Pop-Location
        Write-Host "[WAIT] Waiting for services to be healthy..." -ForegroundColor Yellow

        # Wait for Postgres
        $pgReady = $false
        for ($i = 0; $i -lt 20; $i++) {
            Start-Sleep -Seconds 2
            try {
                $result = docker compose -f "$composeDir\docker-compose.yml" exec postgres pg_isready -U shopagent 2>&1
                if ($LASTEXITCODE -eq 0) { $pgReady = $true; break }
            } catch { }
            Write-Host "  Postgres: waiting... ($i/20)" -ForegroundColor DarkGray
        }
        if ($pgReady) { Write-Host "  Postgres: READY" -ForegroundColor Green }
        else { Write-Host "  Postgres: TIMEOUT (may still be starting)" -ForegroundColor Yellow }

        # Wait for Qdrant
        $qdReady = $false
        for ($i = 0; $i -lt 20; $i++) {
            Start-Sleep -Seconds 2
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:6333/healthz" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
                if ($response.StatusCode -eq 200) { $qdReady = $true; break }
            } catch { }
            Write-Host "  Qdrant: waiting... ($i/20)" -ForegroundColor DarkGray
        }
        if ($qdReady) { Write-Host "  Qdrant: READY" -ForegroundColor Green }
        else { Write-Host "  Qdrant: TIMEOUT (may still be starting)" -ForegroundColor Yellow }
    } else {
        Write-Host "  Postgres: RUNNING" -ForegroundColor Green
        Write-Host "  Qdrant:  RUNNING" -ForegroundColor Green
    }

    # Quick connectivity test
    Write-Host ""
    Write-Host "[CHECK] Connectivity..." -ForegroundColor White -NoNewline
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:6333/healthz" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        Write-Host " OK" -ForegroundColor Green
    } catch {
        Write-Host " FAILED (Qdrant not reachable on :6333)" -ForegroundColor Red
        Write-Host "  Run: docker compose -f gen\docker-compose.yml up -d" -ForegroundColor Yellow
    }
}

# ── Activate venv ──────────────────────────────────────────────────
$venvPaths = @(
    (Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"),
    (Join-Path (Split-Path $ProjectRoot) ".venv\Scripts\Activate.ps1")
)
$activated = $false
foreach ($vp in $venvPaths) {
    if (Test-Path $vp) {
        . $vp
        Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
        $activated = $true
        break
    }
}
if (-not $activated) {
    Write-Host "[WARN] No .venv found — using system Python" -ForegroundColor Yellow
}

# ── Launch Chainlit ────────────────────────────────────────────────
$appPath = Join-Path $ProjectRoot "src\day$Day\chainlit_app.py"
if (-not (Test-Path $appPath)) {
    Write-Host "[FAIL] Chainlit app not found: $appPath" -ForegroundColor Red
    exit 1
}

$port = if ($Day -eq 3) { 8000 } elseif ($Day -eq 4) { 8001 } else { 8000 }

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Launching ShopAgent Day $Day" -ForegroundColor Cyan
Write-Host "  URL: http://localhost:$port" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $ProjectRoot
chainlit run $appPath --port $port
