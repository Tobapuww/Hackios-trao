# Hackios-trao

**HakiOS device layer — OnePlus Ace Pro (PGP110) / OnePlus 10T (AQ101, global), Qualcomm Cape / SM8475.**

This repository holds only the **device adaptation layer** for this phone: device configuration, SoC hardware facts, the UEFI platform package sources, porting scripts and device-tree facts. The HakiOS common kernel, loader and generic drivers live in the common repository. Following the official HakiOS "one repository per device" layout, this is the `pgp110` device repository.

> This is a **research port**. The device now boots to the desktop: touch scrolling and keys work, and all 8 cores are online. Every subsystem below is marked with its current availability and evidence boundary — read "Current status" before using anything here.

[中文](README.md) | English

## Supported devices

| Market name | Codename | Region | Notes |
|---|---|---|---|
| OnePlus Ace Pro | PGP110 | China mainland | Every fact in this repo was captured from a PGP110 unit |
| OnePlus 10T | AQ101 | Global | Same Cape / SM8475 hardware; parameters and device tree must be re-verified on an AQ101 unit |

### Hardware summary (from the device's own tree and `/proc/iomem`)

| Item | Value |
|---|---|
| SoC | Qualcomm Snapdragon 8+ Gen 1, Cape / SM8475 (`soc_id` 530, machine `CAPE`) |
| CPU | 8 cores (all online) |
| GPU | Adreno 730, gen7-4-0 (`qcom,chipid 0x7030002`) |
| RAM | 16 GB (`MemTotal` 15 583 640 kB) |
| Storage | UFS, `ufshc@1d84000` |
| Display | 1080 × 2412, DSC command mode, panel `ovaltine_boe_nt37705` |
| Touch | Synaptics S3910 on SE4 SPI (gpio16/17/18/19), INT gpio21, RESET gpio20, 1.8 V enable gpio97 |
| Wi-Fi | Qualcomm QCA6490 on PCIe0 / MHI |
| PMIC | pm8350 / pm8350b / pm8350c, pmr735a / pmr735b, pm8450, pm8010i / pm8010j |

## Current status

Status scale: **works** — usable on device; **partial** — some progress or a single experiment, not stably usable; **missing** — not started, or facts collected only. Evidence and gaps are in `soc/`, `uefi/STATUS.md` and `device.conf`.

| Subsystem | Status | Current progress and what remains |
|---|---|---|
| UEFI platform package | partial | The Mu-Silicium platform skeleton parses in the toolchain; a local build with this unit's vendor RawFiles once produced an FD image (49 images verified). `MemoryMapLib` / `ConfigurationMapLib` still carry reference-phone numbers; the FD load address is not verified item-by-item on device. |
| Kernel SoC layer | partial | Defconfig and config fragment are authored; all 8 cores are online; other common drivers remain disabled for this device, and register maps have not been checked against the local device tree. |
| Boot chain (BootShim → UEFI → XNU) | works | Boots to the desktop (BootShim → UEFI → XNU → userland). |
| Display | works | Panel lit at 1080 × 2412; the desktop renders and scrolls with touch. |
| Touch (S3910) | works | Synaptics S3910 wired up; touch events and scrolling are usable; wiring recipe in `tools/port-s3910-pgp110.py`. |
| Buttons | works | Keys detected and usable on device. |
| CPU | works | All 8 cores online. |
| GPU (Adreno 730) | partial | In one boot the 18-step power-up sequence passed: GMU firmware loaded, zap shader authenticated, 3D core wrote memory, HakiosGPU service up; Mesa rendering and UI acceleration are not confirmed. |
| Storage (UFS) | partial | The root filesystem mounts over UFS on the way to the desktop; the `ufshc@1d84000` register map is still unchecked against this device tree; the reference driver is only a template. |
| Wi-Fi (QCA6490) | partial | PCIe0 / MHI addresses, pins and power-rail facts are collected (`soc/wifi.md`, `soc/wifi/pgp110-pcie.h`, `configs/pgp110-wifi-sm8475.json`); the PCIe/MHI driver is not written, DMA/MSI untested. |
| Bluetooth | missing | Not started. |
| Audio | missing | ADSP firmware and codec not ported. |
| Battery | missing | Level is reported through the ADSP, not ported. |
| Haptic | missing | Not attempted. |
| Camera | missing | Not attempted. |
| Cellular | missing | Modem firmware not pulled; IPA layout differs from the reference. |
| Thermal | missing | Zones exist; no driver reads them yet. |

### Local experiments (not in this repo, not reproducible from it)

- One experiment unpacked the Darwin userland and built APFS images locally, reaching launchd at one point. The Apple IPSW and userland images are Apple assets and are not distributed here.
- The single-boot GPU evidence came from a local WSL full working tree. This repo keeps only the porting recipes and fact documents; it contains no corresponding driver binaries or experiment logs.

## Repository layout

```
Hackios-trao/
├── device.conf                      # Device identity and per-subsystem availability (read by hakios-device.py)
├── soc.args                        # SoC address / PAS / IPA boot-argument facts
├── pull-firmware.sh                # Pull vendor firmware from the local Android to local fw-* (never committed)
├── configs/
│   ├── pgp110_defconfig            # defconfig: common + sm8475 + this device fragment
│   ├── pgp110.config               # This device's driver switch fragment
│   └── pgp110-wifi-sm8475.json     # Wi-Fi / PCIe0 fact table (local device tree + Android logs)
├── soc/
│   ├── soc.conf
│   ├── configs/sm8475.config
│   ├── hardware.md                  # Local peripheral addresses, PMIC, thermal zones, display, storage facts
│   ├── gpu.md                       # Adreno 730 register blocks, firmware and port checklist
│   ├── wifi.md                      # QCA6490 / PCIe0 / MHI facts and integration plan
│   └── wifi/pgp110-pcie.h           # C header generated from the facts
├── uefi/
│   ├── README.md                    # UEFI platform package plan and checklist
│   ├── STATUS.md                    # Platform package build and on-device audit record
│   └── files/
│       ├── Platforms/OnePlus/pgp110Pkg/   # Mu-Silicium platform package sources (dsc/dec/fdf/sources/libs/tests)
│       ├── Resources/Configs/pgp110.toml  # FD base/size, boot image parameters
│       ├── Resources/DTBs/pgp110.dtb      # Local device tree
│       └── Binaries/pgp110/README.md     # Vendor binary note (the binaries themselves are not committed)
├── prebuilt/
│   ├── BootShim.bin                # BootShim placeholder (built from Mu BootShim source at build time)
│   ├── device-tree.dtb             # Local device-tree fact
│   ├── mkbootimg.py                 # AOSP boot image packer (Apache-2.0)
│   └── ramdisk                     # Placeholder ramdisk
└── tools/                          # Porting and probe scripts (used inside a full HakiOS working tree)
```

## Build

This repo is a device layer and cannot produce a bootable image on its own; it must be paired with the full HakiOS common source tree.

### Kernel configuration

```sh
# In a full HakiOS working tree, place this repo at devices/pgp110/
make pgp110_defconfig
# Build the kernel per the common repository docs:
make kernel DEVICE=pgp110
```

### UEFI platform package

The package sources are under `uefi/files/Platforms/OnePlus/pgp110Pkg/` and are built inside the Mu-Silicium tree with the common build scripts. Vendor DXEs and panel RawFiles must be extracted locally from **your own phone firmware** (see `uefi/files/Binaries/pgp110/README.md`); this repo does not ship those binaries.

### Pull this phone's firmware (local, never committed)

```sh
# Phone on adb in Android; firmware lands in the working tree fw-wifi/, fw-gpu/, excluded by .gitignore
./pull-firmware.sh
```

## What is not in this repo (source boundary)

- **Vendor UEFI binaries**: DXEs `.efi` / `.inf` and panel RawFiles extracted from the `uefi_a` partition; Qualcomm / OnePlus property.
- **Device firmware**: GPU (`gmu_gen70000.bin`, `a730_sqe.fw`, `a730_zap.*`), Wi-Fi (`amss20.bin`, `amss.bin`, `m3.bin`, `regdb.bin`, `bdwlang.b0c`), audio DSP, modem, haptic, camera firmware.
- **Apple assets**: IPSW, Darwin userland images, dyld cache, cryptex, SDKs.
- **Runtime artifacts**: logs, memory dumps, snapshots, backup images, APFS images, experiment data.

Each of these is obtained by the user from their own device and firmware; this repo does not redistribute or embed copies.

## Binary and fact provenance

| File | Source | Handling |
|---|---|---|
| `prebuilt/device-tree.dtb` and the two DTB copies | Captured from the device's `/sys/firmware/fdt` | Hardware fact, pending review; kept as a build input |
| `prebuilt/BootShim.bin` | Built from Mu BootShim source | Open-built artifact, placeholder copy |
| `prebuilt/mkbootimg.py` | Android Open Source Project | Apache-2.0, upstream tool unchanged |
| UEFI platform package sources | Derived from Project Mu / Mu-Silicium | BSD-2-Clause-Patent, marked in file headers |

## License

Our own code in this repo (device config, SoC facts, platform package sources, scripts, documentation) is released under the MIT license; third-party components and their licenses are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Device firmware, the Apple operating system and trademarks are not part of this repository and are not licensed by it.

## Disclaimer

Research port provided as-is, with no warranty of any kind. Before any on-device operation, audit the image's side effects and verify artifact hashes and log retention paths. Do not flash partitions without such an audit; boot firmware from RAM only (`fastboot boot`). The operator bears all risk.
