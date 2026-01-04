#!/usr/bin/env python3
"""
System Health Check TUI
Comprehensive non-destructive diagnostics for SBC systems
Supports: Raspberry Pi (3/4/5), Rock5c

Copyright (C) 2025 Scott Klein

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import subprocess
import re
import json
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich import box
from rich.text import Text

# Configuration
BTRFS_MOUNT_PATH = "/tank"

console = Console()


def run_command(cmd):
    """Run a shell command and return output, returning None on failure."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()
    except Exception as e:
        return None


def detect_board_model():
    """Detect which SBC model we're running on."""
    model_info = run_command("cat /proc/device-tree/model")
    if not model_info:
        return "Unknown"

    # Extract the board model
    if "Raspberry Pi 5" in model_info:
        return "Pi 5"
    elif "Raspberry Pi 4" in model_info:
        return "Pi 4"
    elif "Raspberry Pi 3" in model_info:
        return "Pi 3"
    elif "ROCK 5" in model_info or "Rock 5" in model_info:
        return "Rock5c"
    else:
        return "Unknown"


def detect_nvme_drives():
    """Detect if NVMe drives are present."""
    drives = []
    for drive in ["/dev/nvme0n1", "/dev/nvme1n1"]:
        if os.path.exists(drive):
            drives.append(drive)
    return drives


def detect_btrfs():
    """Detect if btrfs filesystem is mounted at the configured path."""
    mount_info = run_command(f"mount | grep {BTRFS_MOUNT_PATH}")
    if mount_info and "btrfs" in mount_info:
        return True
    return False


def check_reboot_status():
    """Check if a reboot is pending with comprehensive detection methods."""
    reboot_required = False
    reasons = []
    status_level = 0  # 0=OK, 1=WARN, 2=FAIL

    # Check 1: /var/run/reboot-required (Debian/Ubuntu standard)
    if os.path.exists("/var/run/reboot-required"):
        reboot_required = True
        status_level = max(status_level, 1)

        # Try to get the list of packages that require reboot
        packages = []
        if os.path.exists("/var/run/reboot-required.pkgs"):
            try:
                with open("/var/run/reboot-required.pkgs", "r") as f:
                    packages = [pkg.strip() for pkg in f.readlines() if pkg.strip()]
            except:
                pass

        if packages:
            reasons.append(f"Package updates: {', '.join(packages[:5])}")
            if len(packages) > 5:
                reasons.append(f"  ... and {len(packages) - 5} more")
        else:
            reasons.append("Package updates require reboot")

    # Check 2: Kernel version mismatch (running vs installed)
    running_kernel = run_command("uname -r")
    if running_kernel:
        running_kernel = running_kernel.strip()
        # Check what kernel versions are installed
        installed_kernels = run_command("dpkg -l | grep -E 'linux-image-[0-9]' | grep '^ii' | awk '{print $2}' | sed 's/linux-image-//'")
        if installed_kernels:
            installed_list = [k.strip() for k in installed_kernels.split('\n') if k.strip()]
            # Find the newest installed kernel (last in sorted list)
            if installed_list:
                installed_list.sort()
                newest_kernel = installed_list[-1]
                if newest_kernel != running_kernel:
                    reboot_required = True
                    status_level = max(status_level, 1)
                    reasons.append(f"Kernel updated: {running_kernel} → {newest_kernel}")

    # Check 3: Services using deleted libraries (needs restart or reboot)
    deleted_libs = run_command("sudo lsof +c 0 2>/dev/null | grep -E '\\(deleted\\)' | awk '{print $1}' | sort -u")
    if deleted_libs and deleted_libs.strip():
        services = [s.strip() for s in deleted_libs.split('\n') if s.strip() and s.strip() not in ['systemd', 'systemd-journal']]
        if services:
            status_level = max(status_level, 1)
            reasons.append(f"Services using old libraries: {', '.join(services[:5])}")
            if len(services) > 5:
                reasons.append(f"  ... and {len(services) - 5} more")

    # If no reboot is required, return None
    if not reboot_required and status_level == 0:
        return None

    # Create table with results
    border_color = "green"
    if status_level == 2:
        border_color = "red"
    elif status_level == 1:
        border_color = "yellow"

    table = Table(title="System Status", box=box.ROUNDED, show_header=True, expand=True, border_style=border_color)
    table.add_column("Item", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")

    # Main reboot status
    status_text = "[yellow]⚠ YES[/yellow]" if reboot_required else "[green]✓ NO[/green]"
    table.add_row("Reboot Pending", status_text)

    # Add reasons as separate rows
    if reasons:
        for reason in reasons:
            if reason.startswith("  ..."):
                table.add_row("", f"[dim]{reason}[/dim]")
            else:
                table.add_row("Reason", f"[yellow]{reason}[/yellow]")

    return table


def check_firmware_updates(board_model="Unknown"):
    """Check for pending firmware updates (Raspberry Pi only)."""
    # EEPROM updates are only available on Raspberry Pi boards
    if not board_model.startswith("Pi"):
        return None

    update_info = run_command("sudo rpi-eeprom-update")
    
    border_color = "green"
    status_text = "[green]✓ UP TO DATE[/green]"
    
    if not update_info:
        border_color = "red"
        status_text = "[red]✗ FAILED[/red]"
    elif "update available" in update_info:
        border_color = "yellow"
        status_text = "[yellow]⚠ UPDATE AVAILABLE[/yellow]"
    elif "up to date" not in update_info:
        border_color = "yellow"
        status_text = "[yellow]⚠ UNKNOWN[/yellow]"

    table = Table(title="Firmware & EEPROM", box=box.ROUNDED, show_header=True, expand=True, border_style=border_color)
    table.add_column("Component", style="cyan")
    table.add_column("Current")
    table.add_column("Latest")
    table.add_column("Status", style="bold")

    if not update_info:
        table.add_row("Bootloader", "Command failed", "", status_text)
        return table

    current_fw = latest_fw = ""
    for line in update_info.split('\n'):
        stripped_line = line.strip()
        if stripped_line.startswith("CURRENT:"):
            current_fw = stripped_line.split(':', 1)[1].strip()
        elif stripped_line.startswith("LATEST:"):
            latest_fw = stripped_line.split(':', 1)[1].strip()
    
    table.add_row("Bootloader", current_fw, latest_fw, status_text)

    return table


def check_btrfs_health():
    """Check btrfs RAID1 array health"""
    # 1. Gather data and determine status
    status_level = 0  # 0=OK, 1=WARN, 2=FAIL
    rows = []

    # Device stats
    stats_out = run_command(f"sudo btrfs device stats {BTRFS_MOUNT_PATH}")
    if stats_out:
        error_count = 0
        for line in stats_out.split('\n'):
            if 'errs' in line and not line.strip().endswith('0'):
                error_count += 1
        if error_count == 0:
            rows.append(("Device Errors", "No I/O errors detected", "[green]✓ PASS[/green]"))
        else:
            status_level = max(status_level, 2)
            rows.append(("Device Errors", f"{error_count} error types detected", "[red]✗ FAIL[/red]"))

    # Filesystem show
    fs_show_out = run_command(f"sudo btrfs filesystem show {BTRFS_MOUNT_PATH}")
    if fs_show_out:
        devices = len([l for l in fs_show_out.split('\n') if 'devid' in l])
        rows.append(("Devices", f"{devices}/2 devices present", "[green]✓ OK[/green]"))

    # Filesystem usage
    fs_usage_out = run_command(f"sudo btrfs filesystem usage {BTRFS_MOUNT_PATH}")
    if fs_usage_out:
        raid_data = "RAID1" if "RAID1" in fs_usage_out else "Unknown"
        for line in fs_usage_out.split('\n'):
            if 'Data ratio:' in line:
                ratio = line.split(':')[1].strip()
                if ratio == "2.00":
                    rows.append(("RAID Level", f"Data: {raid_data} (ratio: {ratio})", "[green]✓ OK[/green]"))

    # Scrub status
    scrub_out = run_command(f"sudo btrfs scrub status {BTRFS_MOUNT_PATH}")
    if scrub_out:
        if "never run" in scrub_out.lower():
            status_level = max(status_level, 1)
            rows.append(("Last Scrub", "Never run", "[yellow]⚠ WARNING[/yellow]"))
        elif "running" in scrub_out.lower():
            rows.append(("Last Scrub", "Currently in progress", "[blue]⟳ RUNNING[/blue]"))
        elif "finished" in scrub_out.lower() or "aborted" in scrub_out.lower() or "no stats available" in scrub_out.lower():
            error_summary = "not found"
            for line in scrub_out.split('\n'):
                if 'Error summary:' in line:
                    error_summary = line.split(':', 1)[1].strip()
                    break
            if error_summary == "no errors found":
                rows.append(("Last Scrub", "Completed without errors", "[green]✓ OK[/green]"))
            elif error_summary != "not found":
                status_level = max(status_level, 2)
                rows.append(("Last Scrub", f"Errors found: {error_summary}", "[red]✗ FAIL[/red]"))
            elif "0 errors found" in scrub_out.lower(): # Fallback for old versions
                rows.append(("Last Scrub", "Completed without errors", "[green]✓ OK[/green]"))
            else:
                status_level = max(status_level, 1)
                rows.append(("Last Scrub", "Could not determine error status", "[yellow]⚠ CHECK[/yellow]"))
        else:
            status_level = max(status_level, 1)
            rows.append(("Last Scrub", "Status unclear", "[yellow]⚠ UNKNOWN[/yellow]"))

    # Balance status
    balance_info = None
    cmd_service = "sudo journalctl -u btrfs-balance.service --no-pager -o json | grep -i 'finished with status' | tail -n 1"
    log_service_json = run_command(cmd_service)
    if log_service_json:
        try:
            data = json.loads(log_service_json)
            balance_info = {'timestamp': int(data['__REALTIME_TIMESTAMP']), 'message': data.get("MESSAGE", ""), 'source': 'service'}
        except (json.JSONDecodeError, KeyError, ValueError): pass
    cmd_kernel = "sudo journalctl -k --no-pager -o json | grep -i 'balance: ended' | tail -n 1"
    log_kernel_json = run_command(cmd_kernel)
    if log_kernel_json:
        try:
            data = json.loads(log_kernel_json)
            ts = int(data['__REALTIME_TIMESTAMP'])
            if not balance_info or ts > balance_info['timestamp']:
                balance_info = {'timestamp': ts, 'message': '', 'source': 'kernel'}
        except (json.JSONDecodeError, KeyError, ValueError): pass

    if balance_info:
        days_ago = (datetime.now() - datetime.fromtimestamp(balance_info['timestamp'] / 1_000_000)).days
        details = f"Ran {days_ago} days ago ({balance_info['source']})"
        status_text = ""
        if balance_info['source'] == 'service' and 'status 0' not in balance_info['message']:
            status_level = max(status_level, 2)
            status_text = "[red]✗ FAIL[/red]"
        elif days_ago > 30:
            status_level = max(status_level, 1)
            status_text = "[yellow]⚠ WARNING[/yellow]"
        else:
            status_text = "[green]✓ OK[/green]"
        rows.append(("Last Balance", details, status_text))
    else:
        rows.append(("Last Balance", "Not found in logs", "[dim]—[/dim]"))

    # 2. Determine border color
    border_color = "green"
    if status_level == 2:
        border_color = "red"
    elif status_level == 1:
        border_color = "yellow"

    # 3. Create and populate table
    table = Table(title=f"btrfs RAID1 Health ({BTRFS_MOUNT_PATH})", box=box.ROUNDED, show_header=True, expand=True, border_style=border_color)
    table.add_column("Check", style="cyan")
    table.add_column("Details")
    table.add_column("Status", style="bold")
    for row in rows:
        table.add_row(*row)

    return table


def check_nvme_health(drives=None):
    """Check NVMe drive SMART health"""
    if not drives:
        drives = []

    # 1. Gather data and determine status
    status_level = 0  # 0=OK, 1=WARN, 2=FAIL
    drive_results = []

    for drive in drives:
        result = {"drive": drive.split('/')[-1], "model": "N/A", "temp": "-", "wear": "-", "health_status": "[red]✗ NO DATA[/red]"}
        smart_json = run_command(f"sudo smartctl -aj {drive}")

        if not smart_json:
            status_level = max(status_level, 2)
        else:
            try:
                data = json.loads(smart_json)
                result["model"] = data.get("model_name", "Unknown")
                result["model"] = result["model"][:25] + "..." if len(result["model"]) > 25 else result["model"]
                
                health = data.get("smart_status", {}).get("passed", False)
                if health:
                    result["health_status"] = "[green]✓ PASSED[/green]"
                else:
                    status_level = max(status_level, 2)
                    result["health_status"] = "[red]✗ FAILED[/red]"

                temp = data.get("temperature", {}).get("current", "-")
                result["temp"] = f"{temp}°C" if isinstance(temp, int) else "-"

                wear = data.get("nvme_smart_health_information_log", {}).get("percentage_used", "-")
                result["wear"] = f"{wear}%" if isinstance(wear, int) else "-"
            
            except json.JSONDecodeError:
                status_level = max(status_level, 2)
                result["health_status"] = "[red]✗ JSON ERROR[/red]"
        
        drive_results.append(result)

    # 2. Determine border color
    border_color = "green"
    if status_level == 2:
        border_color = "red"
    
    # 3. Create and populate table
    table = Table(title="NVMe Drive Health", box=box.ROUNDED, show_header=True, expand=True, border_style=border_color)
    table.add_column("Drive", style="cyan")
    table.add_column("Model")
    table.add_column("Temperature")
    table.add_column("Wear")
    table.add_column("Health", style="bold")

    for res in drive_results:
        table.add_row(res["drive"], res["model"], res["temp"], res["wear"], res["health_status"])

    return table


def check_temperatures_and_power(board_model="Unknown"):
    """Check system temperatures, fan, and power status"""
    # 1. Gather data and determine status level
    status_level = 0  # 0=OK, 1=WARN, 2=FAIL

    # CPU temp data - try vcgencmd first (Pi only), then fallback to sysfs
    cpu_temp_val = None
    cpu_temp_str = "N/A"
    cpu_status_text = "[yellow]⚠ UNKNOWN[/yellow]"

    # Try vcgencmd for Raspberry Pi
    if board_model.startswith("Pi"):
        cpu_temp_out = run_command("vcgencmd measure_temp")
        if cpu_temp_out:
            temp_match = re.search(r"temp=([\d.]+)'C", cpu_temp_out)
            if temp_match:
                cpu_temp_val = float(temp_match.group(1))

    # Fallback: try reading from sysfs (works on all boards)
    if cpu_temp_val is None:
        temp_sysfs = run_command("cat /sys/class/thermal/thermal_zone0/temp")
        if temp_sysfs and temp_sysfs.isdigit():
            cpu_temp_val = float(temp_sysfs) / 1000.0

    # Evaluate temperature if we got it
    if cpu_temp_val is not None:
        cpu_temp_str = f"{cpu_temp_val:.1f}°C"
        if cpu_temp_val >= 75:
            status_level = max(status_level, 2)
            cpu_status_text = "[red]✗ HOT[/red]"
        elif cpu_temp_val >= 60:
            status_level = max(status_level, 1)
            cpu_status_text = "[yellow]⚠ WARM[/yellow]"
        else:
            cpu_status_text = "[green]✓ GOOD[/green]"

    # Fan status data (board-specific)
    fan_label = None
    if board_model == "Pi 5":
        # Pi 5 uses cooling_device0 for fan
        fan_state = run_command("cat /sys/class/thermal/cooling_device0/cur_state")
        if fan_state:
            fan_labels = {0: "off", 1: "low", 2: "medium"}
            fan_label = fan_labels.get(int(fan_state), "high").capitalize()
        else:
            fan_label = "Unknown"
    elif board_model == "Rock5c":
        # Rock5c uses cooling_device4 for PWM fan (states 0-4)
        fan_state = run_command("cat /sys/class/thermal/cooling_device4/cur_state")
        if fan_state:
            try:
                state = int(fan_state)
                fan_labels = {0: "Off", 1: "Low", 2: "Medium", 3: "High", 4: "Max"}
                fan_label = fan_labels.get(state, f"State {state}")
            except ValueError:
                fan_label = "Unknown"

    # Power status data (Pi only - uses vcgencmd)
    power_value = "N/A"
    power_status_text = "[yellow]⚠ UNKNOWN[/yellow]"

    if board_model.startswith("Pi"):
        # Try to get throttle status (Raspberry Pi only)
        throttled_out = run_command("vcgencmd get_throttled")

        if throttled_out and 'throttled=' in throttled_out:
            try:
                val = int(throttled_out.split('=')[1], 16)
                if val == 0:
                    power_value = "Normal"
                    power_status_text = "[green]✓ OK[/green]"
                else:
                    status_level = max(status_level, 2)
                    power_value = "Problems Detected"
                    power_details_list = []
                    if val & 0x1: power_details_list.append("Under-voltage now")
                    if val & 0x10000: power_details_list.append("Under-voltage occurred")
                    if val & 0x4: power_details_list.append("Currently throttled")
                    if val & 0x40000: power_details_list.append("Throttling has occurred")
                    if val & 0x2: power_details_list.append("ARM frequency capped now")
                    if val & 0x20000: power_details_list.append("ARM frequency capping occurred")
                    if val & 0x8: power_details_list.append("Soft temperature limit active")
                    if val & 0x80000: power_details_list.append("Soft temperature limit occurred")
                    power_details = ", ".join(power_details_list)
                    power_status_text = f"[red]✗ FAIL[/red]\n{power_details}"
            except (ValueError, IndexError):
                pass  # Keep unknown status
    else:
        # For non-Pi boards, power monitoring is not available via vcgencmd
        power_value = "Not available"
        power_status_text = "[dim]—[/dim]"

    # 2. Determine border color
    border_color = "green"
    if status_level == 2:
        border_color = "red"
    elif status_level == 1:
        border_color = "yellow"

    # 3. Create and populate table
    table = Table(title="Temperature, Cooling & Power", box=box.ROUNDED, show_header=True, expand=True, border_style=border_color)
    table.add_column("Item", style="cyan")
    table.add_column("Value")
    table.add_column("Status", style="bold")

    table.add_row("CPU Temperature", cpu_temp_str, cpu_status_text)
    # Only show fan status if available
    if fan_label is not None:
        table.add_row("Fan Speed", fan_label, "[green]✓ OK[/green]")
    # Only show power status if not "Not available"
    if power_value != "Not available":
        table.add_row("Power", power_value, power_status_text)

    return table


def check_sd_card():
    """Check microSD/eMMC card health indicators"""
    # 1. Gather data
    status_level = 0 # 0=OK, 1=WARN, 2=FAIL
    rows = []

    # Detect which mmcblk device is used for root filesystem
    root_device = run_command("df / | tail -n 1 | awk '{print $1}'")
    mmcblk_device = None
    if root_device:
        # Extract mmcblk device name (e.g., /dev/mmcblk0p2 -> mmcblk0)
        import re
        match = re.search(r'(mmcblk\d+)', root_device)
        if match:
            mmcblk_device = match.group(1)

    if not mmcblk_device:
        # Fallback to mmcblk0 if detection fails
        mmcblk_device = "mmcblk0"

    # Detect device type (eMMC vs SD)
    device_type_raw = run_command(f"cat /sys/block/{mmcblk_device}/device/type")
    is_emmc = device_type_raw == "MMC" if device_type_raw else False
    device_type_label = "eMMC" if is_emmc else "microSD"

    # Card info
    card_name = run_command(f"cat /sys/block/{mmcblk_device}/device/name")
    card_date = run_command(f"cat /sys/block/{mmcblk_device}/device/date")
    if card_name and card_date:
        rows.append(("Card Model", f"{card_name} (Mfg: {card_date})", "[green]✓[/green]"))

    # eMMC-specific health checks
    if is_emmc:
        # Life time estimation (Type A - SLC mode, Type B - MLC mode)
        life_time_a = run_command(f"cat /sys/block/{mmcblk_device}/device/life_time 2>/dev/null | cut -d' ' -f1")
        life_time_b = run_command(f"cat /sys/block/{mmcblk_device}/device/life_time 2>/dev/null | cut -d' ' -f2")

        if life_time_a and life_time_b:
            try:
                # Convert hex values to int (they're typically in format like 0x01)
                lt_a = int(life_time_a, 16) if life_time_a.startswith('0x') else int(life_time_a)
                lt_b = int(life_time_b, 16) if life_time_b.startswith('0x') else int(life_time_b)

                # Interpret life time values (0x01-0x0A = 0-100% in 10% increments, 0x0B = exceeded)
                def interpret_life_time(val):
                    if val == 0x00:
                        return "Not defined", 0
                    elif val == 0x0B:
                        return "Exceeded maximum", 2
                    elif val >= 0x01 and val <= 0x0A:
                        percent_range = f"{(val-1)*10}-{val*10}%"
                        warn_level = 2 if val >= 0x09 else (1 if val >= 0x07 else 0)
                        return percent_range, warn_level
                    else:
                        return f"Unknown (0x{val:02x})", 1

                lt_a_str, lt_a_warn = interpret_life_time(lt_a)
                lt_b_str, lt_b_warn = interpret_life_time(lt_b)

                # Use the worse of the two warnings
                life_time_warn = max(lt_a_warn, lt_b_warn)
                status_level = max(status_level, life_time_warn)

                if life_time_warn == 2:
                    life_status = "[red]✗ CRITICAL[/red]"
                elif life_time_warn == 1:
                    life_status = "[yellow]⚠ WARNING[/yellow]"
                else:
                    life_status = "[green]✓ GOOD[/green]"

                rows.append(("eMMC Life (A/B)", f"{lt_a_str} / {lt_b_str}", life_status))
            except (ValueError, IndexError):
                rows.append(("eMMC Life", "Could not parse", "[yellow]⚠ UNKNOWN[/yellow]"))

        # Pre-EOL (End of Life) information
        pre_eol = run_command(f"cat /sys/block/{mmcblk_device}/device/pre_eol_info 2>/dev/null")
        if pre_eol:
            try:
                eol_val = int(pre_eol, 16) if pre_eol.startswith('0x') else int(pre_eol)

                if eol_val == 0x01:
                    eol_str = "Normal"
                    eol_status = "[green]✓ GOOD[/green]"
                elif eol_val == 0x02:
                    eol_str = "Warning (80% reserved blocks used)"
                    eol_status = "[yellow]⚠ WARNING[/yellow]"
                    status_level = max(status_level, 1)
                elif eol_val == 0x03:
                    eol_str = "Urgent (90% reserved blocks used)"
                    eol_status = "[red]✗ CRITICAL[/red]"
                    status_level = max(status_level, 2)
                else:
                    eol_str = f"Unknown (0x{eol_val:02x})"
                    eol_status = "[yellow]⚠ UNKNOWN[/yellow]"

                rows.append(("eMMC Pre-EOL", eol_str, eol_status))
            except (ValueError, IndexError):
                rows.append(("eMMC Pre-EOL", "Could not parse", "[yellow]⚠ UNKNOWN[/yellow]"))

    # Check for errors in dmesg
    errors_out = run_command(f"sudo dmesg | grep -i '{mmcblk_device}.*error' | wc -l")
    if errors_out:
        error_count = int(errors_out)
        if error_count == 0:
            rows.append(("Kernel Errors", "No errors in dmesg", "[green]✓ PASS[/green]"))
        else:
            status_level = max(status_level, 2)
            rows.append(("Kernel Errors", f"{error_count} errors found", "[red]✗ FAIL[/red]"))

    # Check filesystem (look for root device in mount)
    mount_info = run_command(f"mount | grep {mmcblk_device}")
    if mount_info:
        # Check if mounted read-only by looking for (ro, or (ro) in mount options
        # Avoid false positives from "errors=remount-ro" etc.
        if '(ro,' in mount_info or '(ro)' in mount_info:
            status_level = max(status_level, 2)
            rows.append(("Mount Status", "Filesystem is read-only!", "[red]✗ READ-ONLY[/red]"))
        else:
            rows.append(("Mount Status", "Mounted read-write", "[green]✓ OK[/green]"))

    # Check disk usage
    disk_usage_out = run_command("df -h / | tail -n 1 | awk '{print $5}'")
    if disk_usage_out and '%' in disk_usage_out:
        usage_percent = int(disk_usage_out.replace('%', ''))
        details = f"Space used on /"
        if usage_percent > 95:
            status_level = max(status_level, 2)
            status = f"[red]✗ CRITICAL ({usage_percent}%)"
        elif usage_percent > 85:
            status_level = max(status_level, 1)
            status = f"[yellow]⚠ HIGH ({usage_percent}%)"
        else:
            status = f"[green]✓ OK ({usage_percent}%)"
        rows.append(("Disk Usage", details, status))

    # 2. Determine border color
    border_color = "green"
    if status_level == 2:
        border_color = "red"
    elif status_level == 1:
        border_color = "yellow"

    # 3. Create and populate table
    table = Table(title=f"Boot Drive ({device_type_label})", box=box.ROUNDED, show_header=True, expand=True, border_style=border_color)
    table.add_column("Check", style="cyan")
    table.add_column("Details")
    table.add_column("Status", style="bold")

    for row in rows:
        table.add_row(*row)

    return table


def check_led_status():
    """Check status of onboard LEDs (user-controllable status LEDs only)"""
    # 1. Gather data
    status_level = 0  # 0=OK, 1=WARN, 2=FAIL
    rows = []

    # Scan for user-controllable LEDs (exclude activity indicators like mmc, disk, etc.)
    led_dir = "/sys/class/leds"
    if not os.path.exists(led_dir):
        return None

    # Common LED names to look for across different SBCs
    # user-led = green LED on Rock5c
    # blue:status = blue LED on Rock5c
    # ACT, PWR = Raspberry Pi LEDs
    led_patterns = ["user-led", "blue:", "green:", "red:", "ACT", "PWR", "led0", "led1"]

    found_leds = []
    for led_name in os.listdir(led_dir):
        # Skip activity indicators (mmc, disk, etc.)
        if any(skip in led_name for skip in ["mmc", "disk", "input", "phy"]):
            continue

        # Check if it matches our patterns
        if any(pattern in led_name for pattern in led_patterns):
            led_path = os.path.join(led_dir, led_name)

            # Read brightness
            brightness = run_command(f"cat {led_path}/brightness 2>/dev/null")
            trigger = run_command(f"cat {led_path}/trigger 2>/dev/null")

            if brightness is not None and trigger is not None:
                # Parse trigger to find active one (enclosed in brackets)
                import re
                active_trigger_match = re.search(r'\[([^\]]+)\]', trigger)
                active_trigger = active_trigger_match.group(1) if active_trigger_match else "none"

                # Determine LED state
                is_on = int(brightness) > 0 or active_trigger != "none"

                # Friendly LED name
                friendly_name = led_name
                if "user-led" in led_name:
                    friendly_name = "Green LED (user)"
                elif "blue:status" in led_name:
                    friendly_name = "Blue LED (status)"
                elif "ACT" in led_name:
                    friendly_name = "Activity LED"
                elif "PWR" in led_name:
                    friendly_name = "Power LED"

                # Status display
                if is_on:
                    if active_trigger == "none":
                        status = "[green]✓ ON[/green]"
                    else:
                        status = f"[green]✓ ON[/green] ({active_trigger})"
                else:
                    status = "[dim]— OFF[/dim]"

                rows.append((friendly_name, status))
                found_leds.append(led_name)

    # If no LEDs found, don't display this table
    if not rows:
        return None

    # 2. Border color (always green - this is informational only)
    border_color = "green"

    # 3. Create and populate table
    table = Table(title="Onboard LEDs", box=box.ROUNDED, show_header=True, expand=True, border_style=border_color)
    table.add_column("LED", style="cyan")
    table.add_column("Status", style="bold")

    for row in rows:
        table.add_row(*row)

    return table


def check_system_info(board_model="Unknown"):
    """Get general system information"""
    table = Table(title="System Information", box=box.ROUNDED, show_header=False, expand=True, border_style="green")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="bold")

    # Device Model (raw from device tree)
    device_model = run_command("cat /proc/device-tree/model")
    if device_model:
        table.add_row("Device", device_model.strip())

    # Hostname
    hostname = run_command("hostname")
    if hostname:
        table.add_row("Hostname", hostname)

    # OS Distribution - check what we're actually running
    # First check for Ubuntu
    ubuntu_version = run_command("lsb_release -sd 2>/dev/null")
    if ubuntu_version and "Ubuntu" in ubuntu_version:
        # Clean up the quotes that lsb_release adds
        ubuntu_version = ubuntu_version.strip('"')
        table.add_row("OS", ubuntu_version)
    else:
        # Check for Raspberry Pi OS
        pi_os_date = run_command("grep -oP 'Raspberry Pi reference \\K\\d{4}-\\d{2}-\\d{2}' /etc/rpi-issue")
        if pi_os_date:
            table.add_row("Pi OS Image", pi_os_date)
            # Also show Debian version for Pi OS
            debian_version = run_command("cat /etc/debian_version")
            if debian_version:
                table.add_row("Debian Base", debian_version)
        else:
            # Fallback to generic Linux distro detection
            os_name = run_command("cat /etc/os-release | grep '^PRETTY_NAME=' | cut -d'=' -f2")
            if os_name:
                os_name = os_name.strip('"')
                table.add_row("OS", os_name)

    # System package update level
    sys_mods_version = run_command("dpkg -l raspberrypi-sys-mods 2>/dev/null | tail -n 1 | awk '{print $3}'")
    if sys_mods_version and sys_mods_version.startswith("1:"):
        # Extract date from version like "1:20251028+1"
        pkg_date = sys_mods_version.split(':')[1].split('+')[0]
        table.add_row("Pkg Updates", pkg_date)

    # Uptime
    uptime = run_command("uptime -p")
    if uptime:
        table.add_row("Uptime", uptime.replace("up ", ""))

    # Load average
    load = run_command("cat /proc/loadavg | cut -d' ' -f1-3")
    if load:
        table.add_row("Load Average", load)

    # Memory
    mem = run_command("free -h | grep Mem | awk '{print $3 \"/\" $2}'")
    if mem:
        table.add_row("Memory Used", mem)

    # Kernel
    kernel = run_command("uname -r")
    if kernel:
        table.add_row("Kernel", kernel)

    # CPU Information
    cpu_count = run_command("nproc")
    if cpu_count:
        table.add_row("CPU Cores", cpu_count)

    # Check for heterogeneous CPU architecture (big.LITTLE)
    lscpu_output = run_command("lscpu")
    if lscpu_output:
        # Count different CPU models
        cpu_models = []
        lines = lscpu_output.split('\n')
        for i, line in enumerate(lines):
            if 'Model name:' in line:
                model = line.split(':', 1)[1].strip()
                # Find corresponding core count and frequency
                cores = threads = max_freq = None
                for j in range(i-5, min(i+10, len(lines))):
                    if j < 0:
                        continue
                    if 'Core(s) per socket:' in lines[j]:
                        cores = lines[j].split(':', 1)[1].strip()
                    if 'Thread(s) per core:' in lines[j]:
                        threads = lines[j].split(':', 1)[1].strip()
                    if 'CPU max MHz:' in lines[j]:
                        max_freq = lines[j].split(':', 1)[1].strip()

                cpu_models.append({
                    'model': model,
                    'cores': cores,
                    'threads': threads,
                    'max_freq': max_freq
                })

        # Display CPU information
        if len(cpu_models) > 1:
            # Heterogeneous CPU (big.LITTLE)
            # Note: lscpu typically lists efficiency cores first, then performance cores
            for idx, cpu in enumerate(cpu_models):
                if idx == 0:
                    label = "Efficiency"
                elif idx == 1:
                    label = "Performance"
                else:
                    label = f"CPU Group {idx+1}"

                freq_ghz = ""
                if cpu['max_freq']:
                    try:
                        freq_ghz = f" @ {float(cpu['max_freq'])/1000:.2f} GHz"
                    except ValueError:
                        pass

                cores_info = cpu['cores'] if cpu['cores'] else "?"
                threads_info = cpu['threads'] if cpu['threads'] else "1"
                total_threads = int(cores_info) * int(threads_info) if cores_info.isdigit() and threads_info.isdigit() else cores_info

                table.add_row(f"{label} CPU", f"{cores_info}C/{total_threads}T {cpu['model']}{freq_ghz}")
        elif len(cpu_models) == 1:
            # Single CPU type
            cpu = cpu_models[0]
            cores_info = cpu['cores'] if cpu['cores'] else cpu_count
            threads_info = cpu['threads'] if cpu['threads'] else "1"

            freq_info = ""
            if cpu['max_freq']:
                try:
                    freq_info = f" @ {float(cpu['max_freq'])/1000:.2f} GHz"
                except ValueError:
                    pass

            if cores_info and threads_info:
                total_threads = int(cores_info) * int(threads_info) if str(cores_info).isdigit() and str(threads_info).isdigit() else cores_info
                table.add_row("CPU Model", f"{cores_info}C/{total_threads}T {cpu['model']}{freq_info}")
            else:
                table.add_row("CPU Model", f"{cpu['model']}{freq_info}")

    return table


def main():
    """Main health check routine for SBC systems"""
    console.clear()

    # Header
    title = Text("System Health Check", style="bold white on blue", justify="center")
    privilege = "(privileged)" if os.geteuid() == 0 else "(unprivileged)"
    timestamp = Text(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {privilege}", style="dim", justify="center")

    console.print(Panel(title, box=box.DOUBLE))
    console.print(timestamp)
    console.print()

    # Detect hardware capabilities
    with console.status("[bold blue]Detecting hardware...", spinner="dots"):
        board_model = detect_board_model()
        nvme_drives = detect_nvme_drives()
        has_btrfs = detect_btrfs()

    # Run all checks
    with console.status("[bold blue]Running diagnostics...", spinner="dots"):
        all_results_raw = [
            check_reboot_status(),
            check_system_info(board_model),
            check_firmware_updates(board_model),
            check_temperatures_and_power(board_model),
            check_sd_card(),
            check_led_status(),
        ]

        # Only check btrfs if it's mounted
        if has_btrfs:
            all_results_raw.append(check_btrfs_health())

        # Only check NVMe if drives are present
        if nvme_drives:
            all_results_raw.append(check_nvme_health(nvme_drives))

        all_results = [item for item in all_results_raw if item is not None]


    # Analyze results before printing
    has_failures = False
    has_warnings = False
    full_output_str = ""
    with console.capture() as capture:
        for item in all_results:
            console.print(item)
    full_output_str = capture.get()

    if "[red]" in full_output_str:
        has_failures = True
    if "[yellow]" in full_output_str:
        has_warnings = True

    # Display results
    for item in all_results:
        console.print(item)
        console.print()

    # Create dynamic summary
    summary_message = ""
    border_style = "green"
    if has_failures:
        summary_message = "[red]✗ FAIL[/red]: One or more critical checks failed."
        border_style = "red"
    elif has_warnings:
        summary_message = "[yellow]⚠ WARNING[/yellow]: System health has warnings to review."
        border_style = "yellow"
    else:
        summary_message = "[green]✓ OK[/green]: All system health checks passed."
        border_style = "green"

    summary = Panel(
        summary_message,
        title="Summary",
        box=box.ROUNDED,
        border_style=border_style
    )
    console.print(summary)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Health check interrupted by user.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error during health check: {e}[/red]")
