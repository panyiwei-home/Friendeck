#!/usr/bin/env python3
"""
Test script for Steam Integration functionality
"""

import os
import sys
import json
from pathlib import Path

# Add the py_modules directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'py_modules'))

try:
    from steam_integration import (
        get_steam_userdata_path,
        get_shortcuts_vdf_path,
        add_file_to_steam,
        load_shortcuts_from_vdf,
        save_shortcuts_to_vdf
    )
    print("✓ Successfully imported steam_integration module")
except ImportError as e:
    print(f"⚠ steam_integration module not available: {e}")
    print("Skipping steam integration tests.")
    sys.exit(0)

def test_path_detection():
    """Test Steam path detection functions"""
    print("\n--- Testing Steam Path Detection ---")
    
    try:
        userdata_path = get_steam_userdata_path()
        print(f"✓ Found Steam userdata path: {userdata_path}")
    except FileNotFoundError as e:
        print(f"⚠ Steam userdata path not found: {e}")
        # This is OK if Steam is not installed
    
    try:
        shortcuts_path = get_shortcuts_vdf_path()
        print(f"✓ Found shortcuts.vdf path: {shortcuts_path}")
    except FileNotFoundError as e:
        print(f"⚠ shortcuts.vdf path not found: {e}")

def test_vdf_functions():
    """Test VDF read/write functions"""
    print("\n--- Testing VDF Functions ---")
    
    # Create a temporary VDF file for testing
    test_file = "/tmp/test_shortcuts.vdf"
    
    # Test data
    test_data = {
        "shortcuts": {
            "0": {
                "appid": "12345678",
                "AppName": "Test Game",
                "Exe": '"/path/to/test/game"',
                "StartDir": '"/path/to/test"',
                "icon": "",
                "ShortcutPath": "",
                "LaunchOptions": "",
                "IsHidden": 0,
                "AllowDesktopConfig": 1,
                "AllowOverlay": 1,
                "OpenVR": 0,
                "AudioStreaming": 0,
                "Devkit": 0,
                "DevkitGameID": "",
                "DevkitOverrideAppID": 0,
                "LastPlayTime": 0,
                "FlatpakAppID": "",
                "tags": {"0": "test"}
            }
        }
    }
    
    # Test save function
    try:
        success = save_shortcuts_to_vdf(test_file, test_data)
        if success:
            print("✓ Successfully saved test VDF data")
        else:
            print("✗ Failed to save test VDF data")
    except Exception as e:
        print(f"✗ Error saving VDF: {e}")
    
    # Test load function
    try:
        loaded_data = load_shortcuts_from_vdf(test_file)
        if loaded_data and "shortcuts" in loaded_data:
            print("✓ Successfully loaded test VDF data")
            print(f"  Loaded {len(loaded_data['shortcuts'])} shortcuts")
        else:
            print("✗ Failed to load VDF data properly")
    except Exception as e:
        print(f"✗ Error loading VDF: {e}")

def test_add_file_to_steam():
    """Test the add file to Steam functionality"""
    print("\n--- Testing Add File to Steam ---")
    
    # Test with a fake file path to see if the validation works
    result = add_file_to_steam("/fake/path/test.exe")
    
    if result["status"] == "error":
        print("✓ Validation correctly rejected fake file path")
        print(f"  Message: {result['message']}")
    else:
        print(f"✗ Unexpected result for fake file: {result}")

def main():
    print("Testing Steam Integration Module")
    print("="*40)
    
    test_path_detection()
    test_vdf_functions()
    test_add_file_to_steam()
    
    print("\n" + "="*40)
    print("Test completed!")

if __name__ == "__main__":
    main()
