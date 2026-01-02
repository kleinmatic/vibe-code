# Building the Standalone Executable

## Requirements

### Debian/Ubuntu/Armbian
```bash
sudo apt update
sudo apt install -y python3 python3-rich pyinstaller
```

### Fedora/RHEL
```bash
sudo dnf install -y python3 python3-rich pyinstaller
```

### Arch Linux
```bash
sudo pacman -S python python-rich pyinstaller
```

## Build Command

```bash
pyinstaller --onefile --name pi-health-check pi-health-check.py
```

The executable will be created at: `dist/pi-health-check`

## Alternative: Using pip (if system packages aren't available)

```bash
# Install pip if needed
sudo apt install python3-pip  # or equivalent for your distro

# Install dependencies
pip3 install -r requirements.txt
pip3 install pyinstaller

# Build
pyinstaller --onefile --name pi-health-check pi-health-check.py
```

## Notes

- The executable is platform-specific (Linux ARM64 in this case)
- Build on the same architecture you plan to run on
- The resulting binary is ~13MB and contains Python + all dependencies
- No need to install Python or dependencies on the target system
