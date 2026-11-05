# Vendor UEFI binaries — not committed

This directory holds the phone's own UEFI driver binaries and RawFiles
(`*.efi`, `*.inf`, panel XMLs, `SecParti.cfg`, `uefipil.cfg`, …) extracted from
the `uefi_a` partition. They are Qualcomm / OnePlus proprietary and are
**never committed to this repository**.

On a build machine they are produced locally from the user's own firmware:

1. Extract the UEFI firmware volume from the phone's `uefi_a` image.
2. Use [UEFIReader](https://github.com/WOA-Project/UEFIReader) to turn each
   FFS PE32 into `<Name>.efi` plus a binary INF, and to export the RawFiles
   named in the UEFI UI sections.
3. Place them under this directory in the layout the platform package's
   `Include/*.inc` references.

Without these local files the platform package sources in `Platforms/OnePlus/
pgp110Pkg/` can be parsed and reviewed, but a full FD image cannot be linked.
