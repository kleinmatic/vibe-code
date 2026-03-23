# led-control

Single-file LED control for any Linux SBC with `/sys/class/leds` support. Sets LED triggers immediately and optionally persists them across reboots via a self-installing systemd service.

## Usage

```
led-control.sh list                  # show LEDs and current modes
led-control.sh <led> <mode>          # set LED trigger
led-control.sh <led> netdev <iface>  # set LED to network activity
led-control.sh install               # install systemd persistence service
led-control.sh uninstall             # remove systemd service
```

## How It Works

- Sets LED triggers via `/sys/class/leds/<name>/trigger`
- Saves config to `/etc/default/led-<name>` (colons replaced with dashes)
- For netdev mode, interface saved to `/etc/default/led-<name>.interface`
- `install` writes and enables a oneshot systemd service (`led-defaults.service`) that reads those config files on boot
- Without `install`, the script still works for immediate changes and saves configs, but won't survive a reboot

## Tested On

- Radxa Cubie A7A (Allwinner A733)
- Radxa A7Z (Allwinner A527)

## History

- Originated on the Radxa A7Z as a simple LED trigger setter
- Generalized to work on any SBC with `/sys/class/leds`
- Persistence added later: config files were written but nothing read them back on boot
- systemd oneshot service created to close the loop, then embedded into the script via `install`/`uninstall` commands

## Design Decisions

- Single file, no dependencies beyond bash and systemd — easy to scp to a new board
- Config files always written (even without `install`) so persistence is ready when you want it
- The service uses `/bin/sh` (not bash) since it's a simple loop and some SBCs have minimal installs
- `u-boot-update` may regenerate `/boot/extlinux/extlinux.conf` on kernel updates — not related to this script but relevant context for the boards it runs on
