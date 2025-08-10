@echo off
echo Building CallGuard Extension...

REM Check if TypeScript is installed
tsc --version >nul 2>&1
if errorlevel 1 (
    echo TypeScript not found. Installing...
    npm install -g typescript
)

REM Build the extension
echo Compiling TypeScript files...
tsc

REM Copy compiled files to extension root
echo Copying compiled files...
copy dist\*.js . >nul 2>&1

REM Clean up dist folder
if exist dist rmdir /s /q dist

echo Build complete!
echo You can now load the extension in Edge/Chrome from the 'extension' folder.
pause 