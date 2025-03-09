import os
import sys
import platform
import logging
import requests
import zipfile
import shutil
import subprocess
import json
from io import BytesIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('chromedriver_helper')

def get_chrome_version():
    """Get the installed Chrome version."""
    try:
        version = None
        system = platform.system()
        
        if system == "Windows":
            # Use registry query or direct file check
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
                winreg.CloseKey(key)
            except (ImportError, FileNotFoundError):
                # Try direct file check
                chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                if not os.path.exists(chrome_path):
                    chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                
                if os.path.exists(chrome_path):
                    # Use Windows-specific command to get version info
                    result = subprocess.check_output(
                        f'wmic datafile where name="{chrome_path}" get Version /value',
                        shell=True
                    ).decode('utf-8').strip()
                    version = result.split('=')[1] if '=' in result else None
        
        elif system == "Darwin":  # macOS
            # Check standard macOS Chrome location
            try:
                output = subprocess.check_output(
                    ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'],
                    stderr=subprocess.STDOUT
                ).decode('utf-8')
                version = output.strip().split(' ')[-1]
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
        
        elif system == "Linux":
            # Try different commands to check Chrome version on Linux
            commands = [
                ['google-chrome', '--version'],
                ['chrome', '--version'],
                ['chromium', '--version'],
                ['chromium-browser', '--version']
            ]
            
            for cmd in commands:
                try:
                    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8')
                    version = output.strip().split(' ')[-1]
                    break
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
        
        if version:
            # Return just the major version (e.g., "90" from "90.0.4430.212")
            major_version = version.split('.')[0]
            logger.info(f"Detected Chrome version: {version} (Major: {major_version})")
            return major_version
        else:
            logger.warning("Could not detect Chrome version")
            return None
    
    except Exception as e:
        logger.error(f"Error detecting Chrome version: {str(e)}")
        return None

def get_chromedriver_download_url():
    """Get the appropriate ChromeDriver download URL based on the platform and Chrome version."""
    try:
        chrome_version = get_chrome_version()
        
        if not chrome_version:
            # Fallback to latest version if we can't detect Chrome version
            logger.warning("Using latest ChromeDriver version as fallback")
            chrome_version = "latest_release"
        
        # Get the latest ChromeDriver version for this Chrome version
        version_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{chrome_version}"
        response = requests.get(version_url)
        
        if response.status_code != 200:
            # Fallback to latest if version-specific one fails
            logger.warning(f"Could not get version-specific ChromeDriver, falling back to latest")
            version_url = "https://chromedriver.storage.googleapis.com/LATEST_RELEASE"
            response = requests.get(version_url)
            
            if response.status_code != 200:
                logger.error("Failed to determine ChromeDriver version")
                return None
        
        chromedriver_version = response.text.strip()
        
        # Determine platform
        system = platform.system()
        if system == "Windows":
            platform_name = "win32"
        elif system == "Darwin":  # macOS
            platform_name = "mac64"
            # Check for ARM-based Mac (M1/M2)
            if platform.machine() == "arm64":
                platform_name = "mac64_m1"
        else:  # Linux
            platform_name = "linux64"
        
        # Create download URL
        download_url = f"https://chromedriver.storage.googleapis.com/{chromedriver_version}/chromedriver_{platform_name}.zip"
        
        logger.info(f"ChromeDriver download URL: {download_url}")
        return download_url
    
    except Exception as e:
        logger.error(f"Error getting ChromeDriver download URL: {str(e)}")
        return None

def download_and_install_chromedriver(target_path):
    """
    Download and install ChromeDriver to the specified path.
    
    Args:
        target_path: Path where the ChromeDriver should be installed
        
    Returns:
        Path to the installed ChromeDriver or None if failed
    """
    try:
        # Get ChromeDriver download URL
        download_url = get_chromedriver_download_url()
        
        if not download_url:
            logger.error("Could not determine ChromeDriver download URL")
            return None
        
        # Create target directory if it doesn't exist
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Download ChromeDriver zip
        logger.info(f"Downloading ChromeDriver from {download_url}")
        response = requests.get(download_url)
        
        if response.status_code != 200:
            logger.error(f"Failed to download ChromeDriver: {response.status_code}")
            return None
        
        # Extract to memory first
        with zipfile.ZipFile(BytesIO(response.content)) as zip_file:
            # Get the name of the ChromeDriver executable in the zip
            chromedriver_name = None
            for file in zip_file.namelist():
                if file.startswith("chromedriver") and not file.endswith('/'):
                    chromedriver_name = file
                    break
            
            if not chromedriver_name:
                logger.error("Could not find ChromeDriver in the downloaded zip")
                return None
            
            # Extract the ChromeDriver
            with zip_file.open(chromedriver_name) as source, open(target_path, 'wb') as target:
                shutil.copyfileobj(source, target)
        
        # Make it executable (for macOS and Linux)
        if platform.system() != "Windows":
            os.chmod(target_path, 0o755)
        
        logger.info(f"ChromeDriver installed successfully at {target_path}")
        return target_path
    
    except Exception as e:
        logger.error(f"Error downloading and installing ChromeDriver: {str(e)}")
        return None

def ensure_chromedriver(target_path=None):
    """
    Ensure that ChromeDriver is available at the specified path.
    If not, download and install it.
    
    Args:
        target_path: Path where the ChromeDriver should be installed (default: platform-specific)
        
    Returns:
        Path to the ChromeDriver
    """
    # Default path if none provided
    if not target_path:
        # Define default paths based on platform
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        if platform.system() == "Windows":
            target_path = os.path.join(base_dir, "drivers", "chromedriver.exe")
        else:
            target_path = os.path.join(base_dir, "drivers", "chromedriver")
    
    # Check if ChromeDriver already exists at the path
    if os.path.exists(target_path):
        logger.info(f"ChromeDriver already exists at {target_path}")
        return target_path
    
    # Check for ChromeDriver in D:/lead_gen_tool/chromedriver.exe
    fixed_path = "D:/lead_gen_tool/chromedriver.exe"
    if os.path.exists(fixed_path):
        logger.info(f"Found ChromeDriver at fixed path: {fixed_path}")
        return fixed_path
    
    # Download and install ChromeDriver
    return download_and_install_chromedriver(target_path)

if __name__ == "__main__":
    # Run as standalone script
    chromedriver_path = ensure_chromedriver()
    if chromedriver_path:
        print(f"ChromeDriver is available at: {chromedriver_path}")
    else:
        print("Failed to ensure ChromeDriver availability")
        sys.exit(1)
