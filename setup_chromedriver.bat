@echo off
echo ===================================
echo ChromeDriver Setup for Lead Gen Tool
echo ===================================
echo.

:: Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher and try again.
    pause
    exit /b 1
)

:: Create the drivers directory if it doesn't exist
if not exist "drivers\" (
    echo Creating drivers directory...
    mkdir drivers
)

:: Check if D:\lead_gen_tool directory exists, create if not
if not exist "D:\lead_gen_tool\" (
    echo Creating D:\lead_gen_tool directory...
    mkdir "D:\lead_gen_tool"
)

:: Run the ChromeDriver helper script
echo Checking for ChromeDriver and downloading if needed...
python -c "from utils.chromedriver_helper import ensure_chromedriver; ensure_chromedriver('D:/lead_gen_tool/chromedriver.exe')"

if %errorlevel% neq 0 (
    echo.
    echo Error: Failed to download ChromeDriver.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo ChromeDriver setup complete!
echo The driver is now available at D:\lead_gen_tool\chromedriver.exe
echo.
echo You can now run the Lead Generation Tool using the GUI:
echo   python main.py gui
echo.
pause
