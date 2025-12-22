# Raspberry Pi Health Check

A system health monitoring tool for Raspberry Pi systems with a basic terminal UI.

## Features

- **Multi-Model Support**: Automatically detects Pi 3, 4, and 5 models and adapts checks accordingly
- **Temperature Monitoring**: CPU temperature with thermal status
- **Power Status**: Under-voltage and throttling detection
- **Firmware Updates**: Check for pending EEPROM/bootloader updates
- **Storage Health**:
  - microSD card health and usage
  - NVMe drive SMART monitoring (when present)
  - btrfs RAID array health (when configured)
- **System Information**: OS version, uptime, load average, memory usage
- **Privilege Detection**: Shows whether running privileged or unprivileged

## Requirements

- Python 3.7+
- Raspberry Pi running:
  - Raspberry Pi OS (Debian-based)
  - Ubuntu Server
  - Other Debian-based distributions

## Installation

1. Clone or download this repository
2. Install Python dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```
3. Make the script executable:
   ```bash
   chmod +x pi-health-check.py
   ```

## Usage

### Basic Usage

Run without sudo (some checks may show as UNKNOWN):
```bash
./pi-health-check.py
```

Run with sudo for full monitoring capabilities:
```bash
sudo ./pi-health-check.py
```

### Configuration

Edit the configuration section at the top of `pi-health-check.py`:

```python
# Configuration
BTRFS_MOUNT_PATH = "/tank"  # Change to your btrfs mount point
```

## What Gets Checked

### Always Checked
- Reboot pending status
- System information (model, OS, uptime, load, memory)
- Firmware/EEPROM updates
- CPU temperature and power throttling
- microSD card health

### Conditionally Checked
- **Fan speed**: Only on Pi 5 (has active cooling)
- **NVMe drives**: Only when NVMe devices are detected
- **btrfs RAID**: Only when btrfs filesystem is mounted at configured path

## Privilege Requirements

Some checks require elevated privileges:

| Check | Requires sudo? | Notes |
|-------|---------------|-------|
| Temperature | No* | Falls back to sysfs if vcgencmd unavailable |
| Power/Throttling | Yes** | On Ubuntu, vcgencmd needs /dev/vcio access |
| Firmware Updates | Yes | Needs rpi-eeprom-update |
| NVMe SMART | Yes | Requires smartctl with sudo |
| btrfs Health | Yes | All btrfs commands need sudo |
| microSD Health | Partial | Some checks work without sudo |

\* On Raspberry Pi OS: No sudo needed if user is in `video` group
\*\* On Ubuntu Server: Requires sudo or manual `/dev/vcio` setup

## Optional Dependencies

- `smartmontools`: For NVMe drive health monitoring
  ```bash
  sudo apt install smartmontools
  ```
- `btrfs-progs`: For btrfs filesystem checks (usually pre-installed)

## Example Output

```
╔═══════════════════════════════════════════════════════╗
║           System Health Check                          ║
╚═══════════════════════════════════════════════════════╝
         Scan Time: 2024-11-26 14:32:10 (privileged)

╭─── System Information ────╮
│ Model    │ Pi 5           │
│ Hostname │ pi5server      │
│ OS       │ Ubuntu 24.10   │
│ Uptime   │ 5 days, 3 hrs  │
╰───────────────────────────╯
```

## License

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

See the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Troubleshooting

### "UNKNOWN" temperature/power on Ubuntu

On Ubuntu Server, `vcgencmd` requires access to `/dev/vcio`. To fix:

```bash
sudo mknod /dev/vcio c 100 0
sudo chmod 666 /dev/vcio
```

Or create a persistent udev rule - see the [Ubuntu vcgencmd documentation](https://ubuntu.com/tutorials/how-to-install-ubuntu-on-your-raspberry-pi).

### No NVMe or btrfs checks shown

This is expected if you don't have NVMe drives or a btrfs filesystem. The script only shows checks relevant to your hardware.
