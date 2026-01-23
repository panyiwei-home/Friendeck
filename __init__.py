# py_modules - decky-send modular components
#
# NOTE: This __init__.py file is NOT used in the Decky plugin environment.
# 
# Decky automatically adds the py_modules/ directory to sys.path, which means:
# - Modules are imported directly (e.g., "import config") not as package members
# - This __init__.py is never executed by Decky
# - The py_modules directory is NOT treated as a Python package
#
# This file is kept for documentation purposes and potential local development/testing.
#
# Modules:
#   config          - Configuration constants and logger setup
#   utils           - Utility functions (IP address, port checking)
#   file_operations - File system CRUD operations
#   html_templates  - HTML templates and HTTP handlers
#   server_manager  - Server lifecycle management

