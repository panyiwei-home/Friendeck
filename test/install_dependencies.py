#!/usr/bin/env python3
"""
Install dependencies for decky-send Steam integration
"""

import subprocess
import sys
import os

def install_package(package_name):
    """Install a Python package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError:
        print(f"Failed to install {package_name}")
        return False

def main():
    print("Installing dependencies for decky-send Steam integration...")
    
    # List of required packages
    required_packages = [
        "vdf",  # For parsing Valve Data Format files
    ]
    
    # Try to install each package
    for package in required_packages:
        print(f"Installing {package}...")
        install_package(package)
    
    print("Dependency installation complete!")

if __name__ == "__main__":
    main()