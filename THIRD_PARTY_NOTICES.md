# Third-party notices

This repository is the device layer for pgp110. The components below are
either derived from third-party open-source projects or document provenance of
the binary facts kept here.

## Open-source components

| Component | Location | License | Notes |
|---|---|---|---|
| Project Mu / Mu-Silicium platform package | `uefi/files/Platforms/OnePlus/pgp110Pkg/` | BSD-2-Clause-Patent | Derived from the Mu-Silicium tree; per-file SPDX headers apply. Built against the Mu-Silicium source fetched at build time, not vendored here. |
| mkbootimg.py | `prebuilt/mkbootimg.py` | Apache License 2.0 | Android Open Source Project boot image packer; unchanged upstream tool. |
| Device tree blob | `prebuilt/device-tree.dtb`, `uefi/files/Resources/DTBs/pgp110.dtb`, `uefi/files/Platforms/OnePlus/pgp110Pkg/FdtBlob/sm8475-xiaomi-pgp110.dtb` | Hardware fact (pending) | Captured from the phone's own `/sys/firmware/fdt`. It is a vendor device tree; kept as a build input, not a redistributable firmware image. |
| BootShim | `prebuilt/BootShim.bin` | Open-built | Built from the Mu BootShim source at build time; the committed copy is a placeholder fact. |

## Components intentionally NOT committed

- Vendor UEFI driver binaries and RawFiles (`Binaries/pgp110/`): Qualcomm /
  OnePlus, extracted from the phone's `uefi_a` partition. They are rebuilt on
  each user's machine from their own firmware with UEFIReader; see
  `uefi/files/Binaries/pgp110/README.md`.
- GPU firmware (`fw-gpu/`): `gmu_gen70000.bin`, `a730_sqe.fw`, `a730_zap.*` —
  Qualcomm, pulled from the user's own phone by `pull-firmware.sh`.
- Wi-Fi firmware (`fw-wifi/qca6490/`): `amss20.bin`, `amss.bin`, `m3.bin`,
  `regdb.bin`, `bdwlang.b0c` — Qualcomm, pulled from the user's own phone.
- Apple IPSW, Darwin userland images, dyld cache, cryptex: Apple's; fetched and
  unpacked on the user's own machine.
- Runtime logs, memory dumps, snapshots, backup images, APFS images and any
  debug output: local-only artifacts.
