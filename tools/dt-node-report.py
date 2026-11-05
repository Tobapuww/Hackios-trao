#!/usr/bin/env python3
"""Print a device-tree node with its phandles resolved, so the driver constants can be read off it.

usage: dt-node-report.py <dtb> <substring>...
"""
import struct, sys

path = sys.argv[1]
wanted = sys.argv[2:] or ['goodix', 'spi@99']
data = open(path, 'rb').read()
magic, totalsize, off_struct, off_strings = struct.unpack_from('>IIII', data, 0)
assert magic == 0xd00dfeed
strings = data[off_strings:]

def s_at(off):
    return strings[off:strings.index(b'\0', off)].decode()

nodes = []
stack = []
cur = None
off = off_struct
while off < totalsize:
    tok = struct.unpack_from('>I', data, off)[0]
    off += 4
    if tok == 1:
        end = data.index(b'\0', off)
        nm = data[off:end].decode()
        off = (end + 4) & ~3
        cur = {'name': nm, 'path': '/'.join([n['name'] for n in stack] + [nm]), 'props': {}}
        nodes.append(cur)
        stack.append(cur)
    elif tok == 2:
        if stack:
            stack.pop()
        cur = stack[-1] if stack else None
    elif tok == 3:
        ln, nameoff = struct.unpack_from('>II', data, off)
        off += 8
        val = data[off:off + ln]
        off = (off + ln + 3) & ~3
        if cur is not None:
            cur['props'][s_at(nameoff)] = val
    elif tok == 4:
        off = (off + 7) & ~3
    elif tok == 9:
        break

by_phandle = {}
for n in nodes:
    ph = n['props'].get('phandle') or n['props'].get('linux,phandle')
    if ph:
        by_phandle[struct.unpack('>I', ph)[0]] = n

def u32s(v):
    return list(struct.unpack('>%dI' % (len(v) // 4), v)) if len(v) % 4 == 0 else []

def describe(name, val):
    cells = u32s(val)
    if name == 'interrupts' and len(cells) >= 3:
        return 'interrupts = %d, %d, %d (type, number, trigger)' % tuple(cells[:3])
    if name.endswith('gpios') or name in ('gpio',):
        out = []
        for i in range(0, len(cells) - 3, 4):
            target = by_phandle.get(cells[i])
            out.append('gpio %d of %s, flags 0x%x' % (cells[i + 1], target['path'] if target else hex(cells[i]), cells[i + 3]))
        return '%s = %s' % (name, '; '.join(out))
    if name in ('clocks', 'dmas', 'pinctrl-0', 'pinctrl-1', 'pinctrl-2', 'assigned-clocks'):
        out = []
        i = 0
        while i + 1 < len(cells):
            target = by_phandle.get(cells[i])
            out.append('%s[%d]' % (target['name'] if target else hex(cells[i]), cells[i + 1]))
            i += 2
        return '%s = %s' % (name, ', '.join(out))
    if name in ('vdd-supply', 'avdd-supply', 'vddio-supply', 'panel', 'reset-gpio', 'irq-gpio'):
        target = by_phandle.get(cells[0]) if cells else None
        return '%s = %s' % (name, target['path'] if target else (cells[0] if cells else '?'))
    if all(32 <= c < 127 for c in val) and val:
        return '%s = "%s"' % (name, val.decode())
    if cells and len(cells) <= 8:
        return '%s = %s' % (name, ' '.join(str(c) for c in cells))
    return '%s = <%d bytes>' % (name, len(val))

for n in nodes:
    if not any(w in n['name'] for w in wanted):
        continue
    print('\n=== %s' % n['path'])
    for k, v in n['props'].items():
        print('   ', describe(k, v))
