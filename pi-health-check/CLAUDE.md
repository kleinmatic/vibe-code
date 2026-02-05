# Pi Health Check - Claude Code Instructions

## Quick Start

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run TUI mode (default)
./pi-health-check.py

# Run with full privileges (recommended for complete checks)
sudo ./pi-health-check.py

# JSON output for automation
./pi-health-check.py --json

# Build standalone executable
pyinstaller --onefile --name pi-health-check pi-health-check.py
# Output: dist/pi-health-check
```

## Command-Line Options

```
--json      Output results as JSON (for automation/Ansible)
--version   Show version and exit
--help      Show help and exit
```

**Exit codes (--json mode):**
- `0` = All checks passed
- `1` = Warnings detected
- `2` = Failures detected
- `3` = Error running checks

## Project Structure

- `pi-health-check.py` - Main script (single file, ~1500 lines)
- `requirements.txt` - Single dependency: rich>=13.0.0
- `BUILD.md` - PyInstaller build instructions
- `README.md` - User-facing documentation

## Configuration

Btrfs mount path and version are at top of script:
```python
BTRFS_MOUNT_PATH = "/tank"  # Line 38
__version__ = "0.5.1"       # Line 39
```

## Key Architecture

**Single-file design**: All functionality in one Python script

**Main components**:
- Board detection: Pi 3/4/5, Rock5c support
- Health checks: Temperature, throttle/voltage, storage, firmware
- Conditional checks: NVMe, btrfs, fan (Pi 5 only), throttle (Pi only)
- TUI rendering: Rich library for terminal output
- JSON output: Structured data for automation

**Entry point**: Bottom of file, handles CLI args then runs checks

**Dual output modes**:
- TUI mode: `check_*()` functions return Rich Table objects
- JSON mode: `gather_*_data()` functions return dictionaries

## Code Patterns

1. **Command execution**: All system commands use `run_command()` helper (returns None on failure)
2. **Privilege detection**: Checks `os.geteuid() == 0` to adapt behavior
3. **Conditional features**: Auto-detects hardware (NVMe, btrfs) and only shows relevant checks
4. **Status levels**: 0=ok, 1=warning, 2=fail (maps to exit codes in JSON mode)

## JSON Output Structure

```json
{
  "version": "0.5.1",
  "timestamp": "2026-02-01T15:13:22.392731",
  "status": "ok|warning|fail",
  "privileged": true,
  "throttled": { "raw": "0x0", "status": "ok" },
  "system": {
    "device": "Raspberry Pi 5 Model B Rev 1.1",
    "hostname": "pihost",
    "os": "Raspberry Pi OS (2025-10-01)",
    "kernel": "6.12.67-v8-16k+",
    "board_model": "Pi 5",
    ...
  },
  "checks": {
    "reboot": { "status": "ok", "reboot_required": false, ... },
    "temperature": { "status": "ok", "cpu_temp_c": 49.4, "fan_speed": "off" },
    "throttle": {
      "status": "ok|warning|fail",
      "throttle_raw": "0x0",
      "current_flags": [],
      "occurred_flags": []
    },
    "storage": { "status": "ok", "boot_drive": {...}, "nvme": [...], "btrfs": {...} },
    "firmware": { "status": "ok", "update_available": false, ... }
  }
}
```

**Throttle check notes (Pi only):**
- Top-level `throttled` summary: `{"raw": "0x0", "status": "ok"}` for quick Ansible checks
- `current_flags`: Active issues right now (under_voltage, freq_capped, throttled, soft_temp_limit)
- `occurred_flags`: Issues that occurred since boot but may have resolved
- Status: `fail` if current issues, `warning` if only historical, `ok` if none
- `null` on non-Pi boards (Rock5c, etc.)

## Ansible Integration

Example playbook for fleet health monitoring:

```yaml
- name: Check SBC health across fleet
  hosts: pis
  gather_facts: false
  tasks:
    - name: Run health check
      command: /usr/local/bin/pi-health-check --json
      register: health
      failed_when: false
      changed_when: false

    - name: Parse results
      set_fact:
        health_data: "{{ health.stdout | from_json }}"

    - name: Report status
      debug:
        msg: "{{ inventory_hostname }}: {{ health_data.status }} (temp: {{ health_data.checks.temperature.cpu_temp_c }}C)"

    - name: Flag hosts needing attention
      set_fact:
        needs_attention: true
      when: health_data.status != "ok"

    - name: Collect hosts with issues
      debug:
        msg: "WARNING: {{ inventory_hostname }} has status {{ health_data.status }}"
      when: health_data.status != "ok"
```

**Deployment via Ansible:**
```yaml
- name: Deploy pi-health-check
  hosts: pis
  tasks:
    - name: Copy binary
      copy:
        src: dist/pi-health-check
        dest: /usr/local/bin/pi-health-check
        mode: '0755'
```

## Gotchas

1. **Ubuntu vcgencmd issue**: On Ubuntu Server, vcgencmd needs `/dev/vcio` access
   - Falls back to sysfs for temperature if vcgencmd unavailable
   - Throttle check shows UNKNOWN without vcgencmd access

2. **Reboot detection sensitivity**: Multiple methods used to avoid false positives
   - Checks /var/run/reboot-required (Debian/Ubuntu)
   - Checks for modified init scripts
   - LED state detection for some boards

3. **Platform-specific behavior**:
   - Pi 3/4/5: Includes throttle/voltage check (vcgencmd get_throttled)
   - Pi 5: Includes fan speed check
   - Rock5c: Different LED paths, no throttle check (vcgencmd unavailable)
   - Older Pis: Skip fan checks

4. **JSON vs TUI code paths**: Keep both in sync when adding new checks
   - TUI: Add `check_*()` function returning Table
   - JSON: Add `gather_*_data()` function returning dict
   - Update `run_json_checks()` to include new data
   - **IMPORTANT**: When JSON output structure changes, remind user to update Ansible playbooks that consume this data

## Testing

No automated tests. Manual testing required on actual hardware:
- Test unprivileged vs sudo behavior
- Verify on different Pi models (3/4/5)
- Test with/without NVMe drives
- Test with/without btrfs filesystem
- Test `--json` output parses correctly
- Verify exit codes match status (0=ok, 1=warning, 2=fail)

## Deployment

- **Target**: ARM64 Raspberry Pi systems running Debian-based distros
- **Build**: Single standalone executable via PyInstaller (~13MB)
- **Platform-specific**: Build on same architecture as deployment target
