$serverDir = "$PSScriptRoot\pygame-server"

if (-not (Test-Path "$serverDir\node_modules\ws")) {
    npm install --prefix $serverDir
}

nodemon "$serverDir\server.js"
