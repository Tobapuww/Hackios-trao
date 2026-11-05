/** @file
  pgp110: declare the SoC's register window (0x0..0x80000000) as MMIO in the
  DXE memory map, so the ARM CPU arch protocol maps it as device memory when it
  builds the page tables. Without this the XNU loader's native UFS and DWC3
  drivers take a translation fault on their first register read.

  SPDX-License-Identifier: BSD-2-Clause-Patent
**/

#include <Uefi.h>
#include <Library/UefiBootServicesTableLib.h>
#include <Library/DebugLib.h>
#include <Library/DxeServicesTableLib.h>
#include <Pi/PiDxeCis.h>
#include <Library/PrintLib.h>

STATIC CONST UINT64  mIoBase = 0x00000000ULL;
STATIC CONST UINT64  mIoSize = 0x80000000ULL;

EFI_STATUS
EFIAPI
GcdMapEntry (
  IN EFI_HANDLE        ImageHandle,
  IN EFI_SYSTEM_TABLE  *SystemTable
  )
{
  EFI_STATUS  Status;

  Status = gDS->AddMemorySpace (
                  EfiGcdMemoryTypeMemoryMappedIo,
                  mIoBase,
                  mIoSize,
                  0
                  );
  DEBUG ((DEBUG_ERROR, "GcdMap: add %lx..%lx -> %r\n", mIoBase, mIoBase + mIoSize, Status));

  {
    EFI_STATUS  AttrStatus = gDS->SetMemorySpaceAttributes (mIoBase, mIoSize, EFI_MEMORY_UC);
    DEBUG ((DEBUG_ERROR, "GcdMap: UC attributes -> %r\n", AttrStatus));
    {
      CHAR16  Wide[128];
      CHAR8   Line[128];
      AsciiSPrint (Line, sizeof (Line), "GcdMap: add=%r attr=%r\n", Status, AttrStatus);
      UnicodeSPrintAsciiFormat (Wide, sizeof (Wide), "%a", Line);
      if ((SystemTable != NULL) && (SystemTable->ConOut != NULL)) {
        SystemTable->ConOut->OutputString (SystemTable->ConOut, Wide);
      }
    }
  }

  return EFI_SUCCESS;
}
