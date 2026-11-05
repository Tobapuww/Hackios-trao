#!/usr/bin/env python3
"""Port the OnePlus Ace 3 Synaptics S3910 transport to pgp110 and wire it in.

Source: reference OnePlus Ace 3 Synaptics S3910 transport
(hakios.aston_touch.c / hakios.aston_touch_hw.h), kept locally and not committed.
pgp110 wiring (live DTBO, synaptics_tcm@0):
    SPI  gpio16/17/18/19 (SE4)   INT gpio21 (active low)   RESET gpio20 (active low)
    enable1v8_gpio = gpio97 (active high)
"""
import os
import re
import shutil
from pathlib import Path

# Full HakiOS source tree root; override with HAKIOS_TREE. The Ace 3 reference
# kernel tree is passed via ACE3_REF_KERNEL; neither source tree is committed.
H = Path(os.environ.get('HAKIOS_TREE', '.'))
SRC = Path(os.environ.get('ACE3_REF_KERNEL', 'ace3ref/port/kernel'))
DST = H / 'drivers/input'

c = (SRC / 'hakios.aston_touch.c').read_text()
h = (SRC / 'hakios.aston_touch_hw.h').read_text()

# --- the transport keeps its structure; only the wiring and the names change
h = h.replace('#include "hakios.aston_touch_hw.h"', '#include "hakios.s3910_hw.h"')
for old, new in [
    ('#define S39_SPI_MISO    44', '#define S39_SPI_MISO    16'),
    ('#define S39_SPI_MOSI    45', '#define S39_SPI_MOSI    17'),
    ('#define S39_SPI_CLK     46', '#define S39_SPI_CLK     18'),
    ('#define S39_SPI_CS      47', '#define S39_SPI_CS      19'),
    ('#define S39_INT_PIN     25', '#define S39_INT_PIN     21'),
    ('#define S39_RST_PIN     24', '#define S39_RST_PIN     20'),
    ('#define S39_AVDD_PIN    10', '#define S39_AVDD_PIN    97'),
]:
    assert h.count(old) == 1, old
    h = h.replace(old, new)

# the apps RSC base: cape's is 0x17a00000 (DT rsc@17a00000, tcs-offset 0xd00, drv-id 2)
h = re.sub(r'#define S39_RSC_PA\s+0x[0-9a-fA-F]+ULL', '#define S39_RSC_PA     0x17a00000ULL', h)

c = c.replace('#include "hakios.aston_touch_hw.h"', '#include "hakios.s3910_hw.h"')
c = c.replace('hakios_aston_touch_init', 'hakios_s3910_init')
c = c.replace('aston_touch_arg("aston_touch"', 'aston_touch_arg("s3910_touch"')
c = c.replace('aston_touch_arg("aston_touch_ldo"', 'aston_touch_arg("s3910_ldo"')
c = c.replace('s3910: thread start (aston_touch arg set)', 's3910: thread start (s3910_touch set)')
c = c.replace('OnePlus Ace 3 / aston Synaptics S3910 touch screen.',
              'OnePlus Ace Pro (pgp110, cape) Synaptics S3910 touch screen.\n * Ported from the OnePlus Ace 3 (aston) driver: same controller, different wiring\n * (gpio16-19 SPI, INT 21, RESET 20, 1.8 V enable 97).')
c = c.replace('* Boot argument aston_touch=1 opts in.', '* Boot argument s3910_touch=1 opts in.')

(DST / 'hakios.s3910.c').write_text(c)
(DST / 'hakios.s3910_hw.h').write_text(h)

# --- build wiring
conf = H / 'drivers/input/conf'
s = conf.read_text()
if 'driver S3910' not in s:
    s = s.rstrip('\n') + '''

driver S3910
\tfile    bsd/dev/hakios.s3910.c
\tfile    bsd/dev/hakios.s3910_hw.h header
\thelp    the OnePlus Ace Pro's touch screen: a Synaptics S3910 on SE4, gpio16-19, INT 21, RESET 20,
\thelp    1.8 V enable gpio97; bit-bang SPI and the TouchComm (TCM) report layout (s3910_touch=1)
'''
    conf.write_text(s)

mp = H / 'drivers/map'
m = mp.read_text()
if 'hakios.s3910' not in m:
    m = m.replace('input    bsd/dev/hakios.goodix9966.c\n',
                  'input    bsd/dev/hakios.goodix9966.c\ninput    bsd/dev/hakios.s3910.c\ninput    bsd/dev/hakios.s3910_hw.h\n')
    mp.write_text(m)

cfg = H / 'devices/pgp110/configs/pgp110.config'
s = cfg.read_text()
if 'CONFIG_HAKIOS_S3910' not in s:
    s = s.replace('# CONFIG_HAKIOS_GOODIX is not set\nCONFIG_HAKIOS_GOODIX9966=y',
                  '# CONFIG_HAKIOS_GOODIX is not set\nCONFIG_HAKIOS_GOODIX9966=y\nCONFIG_HAKIOS_S3910=y')
    cfg.write_text(s)

print('ported files:', (DST/'hakios.s3910.c').stat().st_size, (DST/'hakios.s3910_hw.h').stat().st_size)
print('RSC line:', [l for l in h.splitlines() if 'S39_RSC_PA' in l])
