Write-Host "Building CallGuard Extension..." -ForegroundColor Green

# Check if TypeScript is installed
try {
    $tscVersion = tsc --version 2>$null
    Write-Host "TypeScript found: $tscVersion" -ForegroundColor Yellow
} catch {
    Write-Host "TypeScript not found. Installing..." -ForegroundColor Yellow
    npm install -g typescript
}

# Build the extension
Write-Host "Compiling TypeScript files..." -ForegroundColor Yellow
tsc

if ($LASTEXITCODE -eq 0) {
    # Copy compiled files to extension root
    Write-Host "Copying compiled files..." -ForegroundColor Yellow
    Copy-Item "dist\*.js" "." -Force
    
    # Clean up dist folder
    Remove-Item "dist" -Recurse -Force -ErrorAction SilentlyContinue
    
    Write-Host "Build complete!" -ForegroundColor Green
    Write-Host "You can now load the extension in Edge/Chrome from the 'extension' folder." -ForegroundColor Cyan
} else {
    Write-Host "Build failed!" -ForegroundColor Red
}

Read-Host "Press Enter to continue" 