"""Port the SM8450 memory map (MU-Qcom gts8) into pgp110Pkg/Library/MemoryMapLib.

The redwood map is for SC7280: its UEFI FD sits at 0x9FD00000 (2 MB) and its
heaps/stacks are at 0x9FFxxxxx / 0xC6D00000. On SM8450 the same pieces are at
0xE5700000 (6 MB), 0xA760xxxx and 0xF8000000, so a redwood map makes the UEFI
allocate memory that is not its own and hang before display.

usage: python tools/port-memmap.py
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'mu-qcom', 'Platforms', 'SM8450Pkg', 'Devices', 'gts8',
                   'Library', 'PlatformMemoryMapLib', 'PlatformMemoryMapLib.c')
DST = os.path.join(ROOT, 'src', 'devices', 'pgp110', 'uefi', 'files', 'Platforms',
                   'OnePlus', 'pgp110Pkg', 'Library', 'MemoryMapLib', 'MemoryMapLib.c')


def main():
    text = open(SRC, encoding='utf-8').read()
    # 1. Mu-Qcom's row struct is the same shape as Mu-Silicium's; only the HOB
    #    option AddDynamicMem does not exist there.
    text = text.replace('AddDynamicMem', 'AddMem')
    # 2. keep only the table body
    m = re.search(r'gDeviceMemoryDescriptorEx\[\] = \{(.*?)\};', text, re.S)
    if not m:
        raise SystemExit('port-memmap: table not found in ' + SRC)
    rows = m.group(1)
    # 3. drop comments that name the tablet
    rows = rows.replace('/* Terminator for MMU */', '/* Terminator for MMU */')

    out = ('#include <Library/MemoryMapLib.h>\n'
           '\n'
           '// Ported from MU-Qcom Platforms/SM8450Pkg/Devices/gts8 (SM8450), not from the\n'
           '// SC7280 reference: the UEFI FD, the heaps and the stacks live elsewhere on this\n'
           '// SoC. Addresses that belong to one board are marked TODO.\n'
           'STATIC\n'
           'EFI_MEMORY_REGION_DESCRIPTOR\n'
           'gMemoryDescriptor[] = {\n'
           '  // Name, Address, Length, HobOption, ResourceType, ResourceAttribute, MemoryType, ArmAttribute\n'
           + rows +
           '};\n'
           '\n'
           'VOID\n'
           'GetMemoryMap (\n'
           '  OUT EFI_MEMORY_REGION_DESCRIPTOR **MemoryDescriptor,\n'
           '  OUT UINT8                         *MemoryDescriptorCount)\n'
           '{\n'
           '  *MemoryDescriptor      = gMemoryDescriptor;\n'
           '  *MemoryDescriptorCount = ARRAY_SIZE (gMemoryDescriptor);\n'
           '}\n')
    open(DST, 'w', newline='\n', encoding='utf-8').write(out)
    print('wrote', DST, len(out), 'bytes')


if __name__ == '__main__':
    main()
