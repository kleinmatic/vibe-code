#!/usr/bin/env python3
"""
System Health Check TUI
Comprehensive non-destructive diagnostics for Raspberry Pi systems

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


def detect_pi_model():
    """Detect which Raspberry Pi model we're running on."""
    model_info = run_command("cat /proc/device-tree/model")
    if not model_info:
        return "Unknown"

    # Extract the Pi model number (e.g., "4", "5")
    if "Raspberry Pi 5" in model_info:
        return "Pi 5"
    elif "Raspberry Pi 4" in model_info:
        return "Pi 4"
    elif "Raspberry Pi 3" in model_info:
        return "Pi 3"
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
    """Check if a reboot is pending. Returns None if no reboot is required."""
    if not os.path.exists("/var/run/reboot-required"):
        return None
    
    border_color = "yellow"
    table = Table(title="System Status", box=box.ROUNDED, show_header=False, expand=True, border_style=border_color)
    table.add_column("Item", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    table.add_row("Reboot Pending", "[yellow]⚠ YES[/yellow]")
    return table


def check_firmware_updates():
    """Check for pending Raspberry Pi firmware updates."""
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


def check_temperatures_and_power(pi_model="Unknown"):
    """Check system temperatures, fan, and power status"""
    # 1. Gather data and determine status level
    status_level = 0  # 0=OK, 1=WARN, 2=FAIL

    # CPU temp data - try vcgencmd first, then fallback to sysfs
    cpu_temp_val = None
    cpu_temp_str = "N/A"
    cpu_status_text = "[yellow]⚠ UNKNOWN[/yellow]"
    cpu_temp_out = run_command("vcgencmd measure_temp")

    if cpu_temp_out:
        temp_match = re.search(r"temp=([\d.]+)'C", cpu_temp_out)
        if temp_match:
            cpu_temp_val = float(temp_match.group(1))

    # Fallback: try reading from sysfs (doesn't need sudo)
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

    # Fan status data (Pi 5 specific)
    fan_label = None
    if pi_model == "Pi 5":
        fan_state = run_command("cat /sys/class/thermal/cooling_device0/cur_state")
        if fan_state:
            fan_labels = {0: "off", 1: "low", 2: "medium"}
            fan_label = fan_labels.get(int(fan_state), "high").capitalize()
        else:
            fan_label = "Unknown"

    # Power status data
    power_value = "N/A"
    power_status_text = "[yellow]⚠ UNKNOWN[/yellow]"

    # Try to get throttle status
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
    # Only show fan status on Pi 5
    if fan_label is not None:
        table.add_row("Fan Speed", fan_label, "[green]✓ OK[/green]")
    table.add_row("Power", power_value, power_status_text)

    return table


def check_sd_card():
    """Check microSD card health indicators"""
    # 1. Gather data
    status_level = 0 # 0=OK, 1=WARN, 2=FAIL
    rows = []

    # Card info
    card_name = run_command("cat /sys/block/mmcblk0/device/name")
    card_date = run_command("cat /sys/block/mmcblk0/device/date")
    if card_name and card_date:
        rows.append(("Card Model", f"{card_name} (Mfg: {card_date})", "[green]✓[/green]"))

    # Check for errors in dmesg
    errors_out = run_command("sudo dmesg | grep -i 'mmcblk0.*error' | wc -l")
    if errors_out:
        error_count = int(errors_out)
        if error_count == 0:
            rows.append(("Kernel Errors", "No errors in dmesg", "[green]✓ PASS[/green]"))
        else:
            status_level = max(status_level, 2)
            rows.append(("Kernel Errors", f"{error_count} errors found", "[red]✗ FAIL[/red]"))

    # Check filesystem
    mount_info = run_command("mount | grep mmcblk0p2")
    if mount_info:
        if 'ro' in mount_info:
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
    table = Table(title="microSD Card (Boot Drive)", box=box.ROUNDED, show_header=True, expand=True, border_style=border_color)
    table.add_column("Check", style="cyan")
    table.add_column("Details")
    table.add_column("Status", style="bold")

    for row in rows:
        table.add_row(*row)

    return table


def check_system_info(pi_model="Unknown"):
    """Get general system information"""
    table = Table(title="System Information", box=box.ROUNDED, show_header=False, expand=True, border_style="green")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="bold")

    # Pi Model
    if pi_model != "Unknown":
        table.add_row("Model", pi_model)

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

    return table


def main():
    """Main health check routine"""
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
        pi_model = detect_pi_model()
        nvme_drives = detect_nvme_drives()
        has_btrfs = detect_btrfs()

    # Run all checks
    with console.status("[bold blue]Running diagnostics...", spinner="dots"):
        all_results_raw = [
            check_reboot_status(),
            check_system_info(pi_model),
            check_firmware_updates(),
            check_temperatures_and_power(pi_model),
            check_sd_card(),
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
