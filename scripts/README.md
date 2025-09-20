# Installation Scripts

This directory contains all installation and deployment scripts.

## Files

- `locallm.bat` - Windows batch file for global command (copy to project root)
- `locallm_entry.py` - Python entry point script for global usage
- `setup_global.py` - Permanent installation script for adding to PATH
- `install.bat` / `install.ps1` - Quick installation scripts
- `verify_install.py` - Installation verification script

## Usage

```bash
# Install globally
python scripts/setup_global.py

# Or use batch file
scripts/install.bat
```