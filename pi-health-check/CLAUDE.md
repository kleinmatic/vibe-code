# Pi Health Check - Claude Code Instructions

## Quick Start

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run directly (unprivileged - some checks will show UNKNOWN)
./pi-health-check.py

# Run with full privileges (recommended for complete checks)
sudo ./pi-health-check.py

# Build standalone executable
pyinstaller --onefile --name pi-health-check pi-health-check.py
# Output: dist/pi-health-check
```

## Project Structure

- `pi-health-check.py` - Main script (single file, ~1200 lines)
- `requirements.txt` - Single dependency: rich>=13.0.0
- `BUILD.md` - PyInstaller build instructions
- `README.md` - User-facing documentation

## Configuration

Btrfs mount path is hardcoded at top of script:
```python
BTRFS_MOUNT_PATH = "/tank"  # Line 38
```

## Key Architecture

**Single-file design**: All functionality in one Python script

**Main components**:
- Board detection: Pi 3/4/5, Rock5c support
- Health checks: Temperature, power, storage, firmware
- Conditional checks: NVMe, btrfs, fan (Pi 5 only)
- TUI rendering: Rich library for terminal output

**Entry point**: Bottom of file, runs all checks and displays results

## Code Patterns

1. **Command execution**: All system commands use `run_command()` helper (returns None on failure)
2. **Privilege detection**: Checks `os.geteuid() == 0` to adapt behavior
3. **Conditional features**: Auto-detects hardware (NVMe, btrfs) and only shows relevant checks

## Gotchas

1. **Ubuntu vcgencmd issue**: On Ubuntu Server, vcgencmd needs `/dev/vcio` access
   - Falls back to sysfs for temperature if vcgencmd unavailable
   - Power/throttling shows UNKNOWN without sudo on Ubuntu

2. **Reboot detection sensitivity**: Multiple methods used to avoid false positives
   - Checks /var/run/reboot-required (Debian/Ubuntu)
   - Checks for modified init scripts
   - LED state detection for some boards

3. **Platform-specific behavior**:
   - Pi 5: Includes fan speed check
   - Rock5c: Different LED paths and detection methods
   - Older Pis: Skip fan checks

## Testing

No automated tests. Manual testing required on actual hardware:
- Test unprivileged vs sudo behavior
- Verify on different Pi models (3/4/5)
- Test with/without NVMe drives
- Test with/without btrfs filesystem

## Deployment

- **Target**: ARM64 Raspberry Pi systems running Debian-based distros
- **Build**: Single standalone executable via PyInstaller (~13MB)
- **Platform-specific**: Build on same architecture as deployment target
