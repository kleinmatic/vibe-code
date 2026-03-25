# led-control

A single-file tool for controlling onboard LEDs on Linux single-board computers. Works with any board that exposes LEDs via `/sys/class/leds` (Radxa, Raspberry Pi, Orange Pi, etc).

## Quick Start

```bash
# Copy to your board
scp led-control user@your-board:~/led-control
ssh user@your-board chmod +x ~/led-control

# See what LEDs are available
./led-control list

# Turn off that annoying blinking blue LED
./led-control blue:user none

# Make it persist across reboots
./led-control install
```

## Usage

```
led-control <command> | <led> [mode] [interface]
```

### Commands

| Command | Description |
|---------|-------------|
| `list` | Show all LEDs and their current modes |
| `triggers <led>` | List available trigger modes for an LED |
| `<led> <mode>` | Set an LED's trigger mode |
| `<led> netdev <iface>` | Set an LED to blink on network activity |
| `install` | Install a systemd service to restore LED settings on boot |
| `uninstall` | Remove the systemd service |

### Modes

| Mode | Effect |
|------|--------|
| `none` | Off |
| `default-on` | Steady on |
| `heartbeat` | Rhythmic pulse (indicates system is alive) |
| `timer` | Configurable blink pattern |
| `cpu` | Blinks on CPU activity |
| `mmc0` | Blinks on storage activity |
| `netdev` | Blinks on network activity (specify interface) |
| `panic` | Blinks on kernel panic |

Not all modes are available on all boards. Use `led-control triggers <led>` to see what your hardware supports.

## Persistence

By default, LED settings revert on reboot because the kernel re-applies its defaults. Running `led-control install` creates a small systemd oneshot service that restores your saved settings at boot.

Settings are saved to `/etc/default/led-*` every time you set a mode, so you can `install` at any time and your current settings will be picked up.

```bash
# Set your LEDs how you like them
./led-control blue:user none
./led-control green:status heartbeat

# Then persist
./led-control install

# Changed your mind? Uninstall is clean
./led-control uninstall
```

## Requirements

- Linux with `/sys/class/leds` support
- bash
- systemd (only for persistence)
- sudo access (LED sysfs files are root-owned)

## Tested On

- Radxa Cubie A7A (Allwinner A733)
- Radxa A7Z (Allwinner A527)

Should work on any Linux SBC. If you test it on another board, let us know!
