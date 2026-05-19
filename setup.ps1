# ── Python 3.12 ───────────────────────────────────────────
$py = py -3.12 --version 2>$null
if ($py) {
    Write-Host "[OK] $py already installed"
} else {
    Write-Host "[Installing] Python 3.12..."
    winget install --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements
    if (-not $?) { Write-Error "Python 3.12 install failed"; exit 1 }
    Write-Host "[OK] Python 3.12 installed"
}

# ── pip packages ──────────────────────────────────────────
foreach ($pkg in @("PyQt6", "pygame", "websocket-client")) {
    $installed = py -3.12 -m pip show $pkg 2>$null
    if ($installed) {
        Write-Host "[OK] $pkg already installed"
    } else {
        Write-Host "[Installing] $pkg..."
        py -3.12 -m pip install $pkg -q
        if (-not $?) { Write-Error "$pkg install failed"; exit 1 }
        Write-Host "[OK] $pkg installed"
    }
}

# ── Node.js ───────────────────────────────────────────────
$node = node --version 2>$null
if ($node) {
    Write-Host "[OK] Node.js $node already installed"
} else {
    Write-Host "[Installing] Node.js..."
    winget install --id OpenJS.NodeJS.LTS --silent --accept-source-agreements --accept-package-agreements
    if (-not $?) { Write-Error "Node.js install failed"; exit 1 }
    Write-Host "[OK] Node.js installed"
}

# ── ws ────────────────────────────────────────────────────
$ws = node -e "require('ws')" --prefix "$PSScriptRoot\pygame-server" 2>$null
if ($?) {
    Write-Host "[OK] ws already installed"
} else {
    Write-Host "[Installing] ws..."
    Push-Location "$PSScriptRoot\pygame-server"
    npm install ws --save
    Pop-Location
    if (-not $?) { Write-Error "ws install failed"; exit 1 }
    Write-Host "[OK] ws installed"
}

# ── nodemon ───────────────────────────────────────────────
$nodemon = nodemon --version 2>$null
if ($nodemon) {
    Write-Host "[OK] nodemon $nodemon already installed"
} else {
    Write-Host "[Installing] nodemon..."
    npm install -g nodemon
    if (-not $?) { Write-Error "nodemon install failed"; exit 1 }
    Write-Host "[OK] nodemon installed"
}

Write-Host ""
Write-Host "Done! Run server: nodemon pygame-server/bin/www"
