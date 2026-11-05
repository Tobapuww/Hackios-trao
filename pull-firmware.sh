#!/bin/bash
# Pull this phone's own firmware out of its Android into the fw-*/ directories at the top of the
# repository (never committed: it is the vendor's). The phone is on adb, in Android.
#
# The Wi-Fi radio is a QCA6490 on PCIe0. Its firmware is five files, not one image:
#   amss20.bin  the firmware the chip actually runs (TCSR/PCI hw major 0x12; amss.bin is hw1)
#   amss.bin    kept for the hw1 fallback
#   m3.bin      the M3 boot loader
#   regdb.bin   the regulatory database
#   bdwlang.b0c the board data file for region 1 / project 21841, from /odm/etc/wifi/qca6490
# They go under fw-wifi/qca6490/ so userland/build.sh can put them into the ramdisk's fw/.
set -e
cd "$(dirname "$0")/../.."

# adb: on PATH (a Linux host), or set ADB=/path/to/adb explicitly.
ADB=${ADB:-}
if [ -z "$ADB" ]; then
	if command -v adb >/dev/null 2>&1; then
		ADB=adb
	else
		echo "pull-firmware.sh: no adb (set ADB=/path/to/adb)" >&2
		exit 1
	fi
fi

"$ADB" get-state >/dev/null

# pull DIR SOURCE...: for files the shell user can read (missing ones are told, not fatal)
pull() {
	local dir=$1; shift
	mkdir -p "$dir"
	for f in "$@"; do
		"$ADB" pull "$f" "$dir/" >/dev/null 2>&1 || echo "pull-firmware.sh: $f: not on the phone (or not readable as shell)"
	done
}

# root_pull DIR SOURCE...: /vendor/firmware_mnt is root-only (dr-xr-x--- system system).
# Stage each file through /sdcard under a name of ours, pull it, remove the copy.
root_pull() {
	local dir=$1; shift
	mkdir -p "$dir"
	for f in "$@"; do
		local name staging
		name=$(basename "$f")
		if "$ADB" pull "$f" "$dir/$name" >/dev/null 2>&1 && [ -s "$dir/$name" ]; then
			continue
		fi
		staging="/sdcard/.hakios-fw-$name"
		if ! "$ADB" shell su -c "cp '$f' '$staging'" >/dev/null 2>&1; then
			echo "pull-firmware.sh: $f: root (su) could not read it"
			continue
		fi
		"$ADB" pull "$staging" "$dir/$name" >/dev/null 2>&1 || echo "pull-firmware.sh: $f: pull failed"
		"$ADB" shell rm -f "$staging" >/dev/null 2>&1 || true
	done
}

root_pull fw-wifi/qca6490 \
	/vendor/firmware_mnt/image/qca6490/amss20.bin \
	/vendor/firmware_mnt/image/qca6490/amss.bin \
	/vendor/firmware_mnt/image/qca6490/m3.bin \
	/vendor/firmware_mnt/image/qca6490/regdb.bin

# The vendor keeps the BDF in /odm, not in the firmware partition; it is world-readable.
pull fw-wifi/qca6490 /odm/etc/wifi/qca6490/bdwlang.b0c

# The GPU and the rest of the phone (kept here so the whole device's firmware is pulled the same way)
pull fw-gpu /vendor/firmware/a730_sqe.fw /vendor/firmware/a730_zap.b00 /vendor/firmware/a730_zap.b01 \
	/vendor/firmware/a730_zap.b02 /vendor/firmware/a730_zap.elf /vendor/firmware/a730_zap.mbn \
	/vendor/firmware/a730_zap.mdt /vendor/firmware/gmu_gen70000.bin

for d in fw-wifi/qca6490 fw-gpu; do
	echo "pull-firmware.sh: $d: $(ls -1 "$d" 2>/dev/null | wc -l | tr -d ' ') files"
done
echo "pull-firmware.sh: done."
echo "pull-firmware.sh: Wi-Fi also wants fw-wifi/mac (the radio's own address) or the driver must take"
echo "                 the one the firmware reports; never invent a factory MAC."
