"""
Configuration utilities for reading and writing YAML-like config files.
"""

import os
import json
from typing import Dict, Any, Callable, Optional


def read_config_yaml(
    config_path: str,
    logger: Callable[[str], None] = None
) -> Dict[str, Any]:
    """
    Read a simple YAML config file.
    
    Args:
        config_path: Path to the config file
        logger: Optional logging callback for errors
    
    Returns:
        Dictionary of config values
    """
    # Ensure directory exists
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
    except Exception as e:
        if logger:
            logger(f"Failed to create config directory: {e}")
        return {}
    
    if not os.path.exists(config_path):
        return {}
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        if logger:
            logger(f"Failed to read config: {e}")
        return {}

    config = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in line:
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.lower() in ("true", "false"):
            value = value.lower() == "true"
        else:
            try:
                value = int(value)
            except ValueError:
                pass
        config[key] = value
    return config


def format_yaml_value(value: Any) -> str:
    """Format a value for YAML output."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    value_str = str(value)
    if value_str == "":
        return '""'
    needs_quote = any(ch in value_str for ch in [":", "#", "\n", "\r", "\t"]) or value_str.startswith(" ") or value_str.endswith(" ")
    return json.dumps(value_str) if needs_quote else value_str


def update_config_yaml(
    config_path: str,
    updates: Dict[str, Any],
    logger: Callable[[str], None] = None
) -> None:
    """
    Update a simple YAML config file.
    
    Args:
        config_path: Path to the config file
        updates: Dictionary of values to update
        logger: Optional logging callback for errors
    """
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    lines = []
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            if logger:
                logger(f"Failed to read config for update: {e}")
            lines = []

    updated_keys = set()
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in line:
            continue
        key, _, _ = stripped.partition(":")
        key = key.strip()
        if key in updates:
            lines[idx] = f"{key}: {format_yaml_value(updates[key])}\n"
            updated_keys.add(key)

    for key, value in updates.items():
        if key in updated_keys:
            continue
        lines.append(f"{key}: {format_yaml_value(value)}\n")

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception as e:
        if logger:
            logger(f"Failed to write config: {e}")


def load_json_settings(
    settings_path: str,
    defaults: Dict[str, Any],
    logger: Callable[[str], None] = None
) -> Dict[str, Any]:
    """
    Load JSON settings file, creating with defaults if it doesn't exist.
    
    Args:
        settings_path: Path to the settings file
        defaults: Default values to use if file doesn't exist
        logger: Optional logging callback
    
    Returns:
        Dictionary of settings
    """
    try:
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        
        # Create default settings file if it doesn't exist
        if not os.path.exists(settings_path):
            if logger:
                logger(f"Settings file not found, creating default: {settings_path}")
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(defaults, f, ensure_ascii=True, indent=2)
            return defaults.copy()
        
        # Load existing settings
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        if logger:
            logger(f"Failed to load settings: {e}")
        return defaults.copy()


def save_json_settings(
    settings_path: str,
    settings: Dict[str, Any],
    logger: Callable[[str], None] = None
) -> bool:
    """
    Save settings to JSON file.
    
    Args:
        settings_path: Path to the settings file
        settings: Settings dictionary to save
        logger: Optional logging callback
    
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=True, indent=2)
        return True
    except Exception as e:
        if logger:
            logger(f"Failed to save settings: {e}")
        return False
