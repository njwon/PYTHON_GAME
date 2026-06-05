#!/bin/bash
set -e

# ── Python 3.12 ───────────────────────────────────────────
if command -v python3.12 &>/dev/null; then
    echo "[OK] Python $(python3.12 --version) already installed"
else
    echo "[Installing] Python 3.12..."
    sudo apt-get update -q
    sudo apt-get install -y python3.12 python3.12-venv python3.12-pip
    echo "[OK] Python 3.12 installed"
fi

# ── pip ───────────────────────────────────────────────────
if ! python3.12 -m pip --version &>/dev/null; then
    echo "[Installing] pip..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12
    echo "[OK] pip installed"
fi

# ── pip packages ──────────────────────────────────────────
for pkg in pygame websocket-client; do
    if python3.12 -m pip show "$pkg" &>/dev/null; then
        echo "[OK] $pkg already installed"
    else
        echo "[Installing] $pkg..."
        python3.12 -m pip install "$pkg" -q
        echo "[OK] $pkg installed"
    fi
done

# ── Node.js ───────────────────────────────────────────────
if command -v node &>/dev/null; then
    echo "[OK] Node.js $(node --version) already installed"
else
    echo "[Installing] Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo apt-get install -y nodejs
    echo "[OK] Node.js installed"
fi

# ── ws ────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if node -e "require('ws')" --prefix "$SCRIPT_DIR/pygame-server" &>/dev/null; then
    echo "[OK] ws already installed"
else
    echo "[Installing] ws..."
    cd "$SCRIPT_DIR/pygame-server"
    npm install
    cd "$SCRIPT_DIR"
    echo "[OK] ws installed"
fi

# ── nodemon ───────────────────────────────────────────────
if command -v nodemon &>/dev/null; then
    echo "[OK] nodemon $(nodemon --version) already installed"
else
    echo "[Installing] nodemon..."
    npm install -g nodemon
    echo "[OK] nodemon installed"
fi

echo ""
echo "Done! Run server: nodemon pygame-server/server.js"
