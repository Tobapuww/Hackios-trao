#!/usr/bin/env python3
"""Bring mayfly's Adreno 730 driver (SM8475, same SoC as pgp110) into this tree and enable it."""
import shutil
from pathlib import Path

H = Path.home() / 'hakios'
MAY = Path.home() / 'hakios-mayfly'

src = MAY / 'drivers/gpu/hakios.adreno7.c'
dst = H / 'drivers/gpu/hakios.adreno7.c'
shutil.copy2(src, dst)
print('copied', dst.name, dst.stat().st_size, 'bytes')

# drivers/gpu/conf: add the driver entry after the ADRENO one
conf = H / 'drivers/gpu/conf'
s = conf.read_text()
if 'driver ADRENO7' not in s:
    s = s.rstrip('\n') + '\n\ndriver ADRENO7\n\tfile    bsd/dev/hakios.adreno7.c\n\trequires GPU\n' \
        '\thelp    the Adreno 730 of the SM8475 (cape), woken step by step (adreno7=N); kept on for HakiosGPU with gpu=1.\n' \
        '\thelp    Needs the GPU firmware in fw-gpu/ (a730_sqe.fw, gmu_gen70000.bin, a730_zap.*)\n'
    conf.write_text(s)
    print('conf entry added')

# drivers/map: every hakios.* file must be listed
mp = H / 'drivers/map'
s = mp.read_text()
if 'hakios.adreno7.c' not in s:
    s = s.replace('gpu      bsd/dev/hakios.adreno.c\n', 'gpu      bsd/dev/hakios.adreno.c\ngpu      bsd/dev/hakios.adreno7.c\n')
    mp.write_text(s)
    print('map entry added')

# pgp110.config: GPU on, ADRENO7 on, a660 driver stays off
cfg = H / 'devices/pgp110/configs/pgp110.config'
s = cfg.read_text()
s = s.replace('# CONFIG_GPU is not set', 'CONFIG_GPU=y')
if 'CONFIG_HAKIOS_ADRENO7' not in s:
    s = s.replace('# CONFIG_HAKIOS_ADRENO is not set', '# CONFIG_HAKIOS_ADRENO is not set\nCONFIG_HAKIOS_ADRENO7=y')
cfg.write_text(s)
print('pgp110.config:', [l for l in cfg.read_text().splitlines() if 'GPU' in l or 'ADRENO' in l])
