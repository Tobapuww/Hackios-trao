"""Generate a pgp110 UEFI platform skeleton from redwoodPkg.

Renames the platform, rewrites the Binaries/ paths and replaces every vendor
driver reference with the name actually extracted from this phone's uefi_a
partition (see uefi-vendor/uefi-inventory.txt).

usage: python tools/make-pgp110-uefi.py

Only mechanical rewriting: MemoryMapLib and ConfigurationMapLib still carry
redwood's numbers and are marked TODO.
"""
import os
import re
import shutil

SRC = os.path.join('src', 'devices', 'redwood', 'uefi', 'files')
DST = os.path.join('src', 'devices', 'pgp110', 'uefi', 'files')
BIN = os.path.join('uefi-vendor', 'Binaries-pgp110-Mu', 'pgp110', 'QcomPkg', 'Drivers')

src_pkg = os.path.join(SRC, 'Platforms', 'Xiaomi', 'redwoodPkg')
dst_pkg = os.path.join(DST, 'Platforms', 'OnePlus', 'pgp110Pkg')

ours = {d for d in os.listdir(BIN) if os.path.isdir(os.path.join(BIN, d))}

# redwood's name -> the name in this phone's UEFI (checked one by one)
SPECIAL = {
    'ChipInfoDxe': 'ChipInfo',
    'DALSYSDxe': 'DALSys',
    'HALIOMMUDxe': 'HALIOMMU',
    'HWIODxe': 'HWIODxeDriver',
    'I2CDxe': 'I2C',
    'GLinkDxe': 'GlinkDxe',
    'PlatformInfoDxe': 'PlatformInfoDxeDriver',
    'ProjectInfoDxe': 'OplusProject',
    'TLMMDxe': 'DALTLMM',
    'SPIDxe': 'SPI',
    'SPMIDxe': 'SPMI',
    'TzDxe': 'TzDxeLA',
    'TzDxeLA': 'TzDxeLA',
    'ScmDxeLA': 'ScmDxeLA',
    'ScmDxe': 'ScmDxeLA',
    'XhciPciEmulationDxe': 'XhciPciEmulation',
    'QcomChargerDxe': 'QcomChargerDxeLA',
}


def pick(ref_name):
    for cand in (SPECIAL.get(ref_name), ref_name,
                 ref_name.replace('DxeLA', 'Dxe'),
                 ref_name.replace('Dxe', ''),
                 ref_name + 'Dxe'):
        if cand and cand in ours:
            return cand
    return None


def rewrite(path):
    text = open(path, encoding='utf-8').read()
    text = text.replace('Binaries/redwood/', 'Binaries/pgp110/')
    text = text.replace('redwoodPkg', 'pgp110Pkg')
    text = text.replace('Platforms/Xiaomi', 'Platforms/OnePlus')
    text = text.replace('"Xiaomi"', '"OnePlus"')
    text = text.replace('POCO_X5_Pro_5G_redwood', 'Ace_Pro_pgp110')
    text = re.sub(r'\bredwood\b', 'pgp110', text)
    # ACPI: redwood uses Xiaomi's lisa/AcpiTables.inf; cape has none yet, so comment every reference
    text = re.sub(r'^(\s*)INF RuleOverride = ACPITABLE\s+\S*AcpiTables\.inf\s*$',
                  r'\1# ACPI tables: TODO (cape), no AcpiTables.inf yet', text, flags=re.M)
    text = re.sub(r'^(\s*)\S*AcpiTables\.inf\s*$',
                  r'\1# ACPI tables: TODO (cape), no AcpiTables.inf yet', text, flags=re.M)
    text = re.sub(r'^(\s*)RuleOverride\s*=\s*ACPITABLE\s*$', r'\1# (ACPI override removed)', text, flags=re.M)
    return text


def remap_inf_lines(text, missing):
    def repl(m):
        # the directory is not always the module's name (TzDxe/ScmDxeLA.inf), so map on the basename
        ref = m.group(2)
        got = pick(ref)
        if got:
            return '  INF Binaries/pgp110/QcomPkg/Drivers/%s/%s.inf' % (got, got)
        missing.add(ref)
        return '  # missing Binaries/pgp110/QcomPkg/Drivers/%s/%s.inf' % (ref, ref)

    return re.sub(r'  INF Binaries/pgp110/QcomPkg/Drivers/([^/]+)/([^/]+)\.inf', repl, text)


def main():
    if os.path.isdir(dst_pkg):
        shutil.rmtree(dst_pkg)
    shutil.copytree(src_pkg, dst_pkg)

    missing = set()
    for root, _dirs, files in os.walk(dst_pkg):
        for f in files:
            p = os.path.join(root, f)
            text = rewrite(p)
            if f.endswith('.inc'):
                text = remap_inf_lines(text, missing)
            with open(p, 'w', newline='\n', encoding='utf-8') as out:
                out.write(text)

    for root, _dirs, files in os.walk(dst_pkg):
        for f in files:
            if 'redwood' in f:
                os.rename(os.path.join(root, f),
                          os.path.join(root, f.replace('redwood', 'pgp110')))

    cfg = os.path.join(DST, 'Resources', 'Configs')
    dtb = os.path.join(DST, 'Resources', 'DTBs')
    os.makedirs(cfg, exist_ok=True)
    os.makedirs(dtb, exist_ok=True)
    shutil.copyfile(os.path.join(SRC, 'Resources', 'Configs', 'redwood.toml'),
                    os.path.join(cfg, 'pgp110.toml'))
    shutil.copyfile('device-tree.dtb', os.path.join(dtb, 'pgp110.dtb'))

    print('platform:', dst_pkg)
    print('drivers available:', len(ours))
    print('missing (no counterpart):', ', '.join(sorted(missing)) or 'none')


if __name__ == '__main__':
    main()
