#!/usr/bin/env python3
"""Dump the pgp110 device tree's touch (and SPI) nodes as plain text.

Uses the phone's own DTB in the repository, so it is the same data the kernel will see.
"""
import struct, sys

path = sys.argv[1] if len(sys.argv) > 1 else 'devices/pgp110/prebuilt/device-tree.dtb'
data = open(path, 'rb').read()
magic, totalsize, off_struct, off_strings = struct.unpack_from('>IIII', data, 0)
assert magic == 0xd00dfeed, hex(magic)

strings = data[off_strings:]

def name_at(off):
    end = strings.index(b'\0', off)
    return strings[off:end].decode()

# parse structure into a flat list of (depth, name, props)
stack, nodes = [], []
off = off_struct
depth = 0
cur = None
while off < totalsize:
    tok = struct.unpack_from('>I', data, off)[0]
    off += 4
    if tok == 1:                      # FDT_BEGIN_NODE
        end = data.index(b'\0', off)
        nm = data[off:end].decode()
        off = (end + 4) & ~3
        cur = {'name': nm, 'depth': len(stack), 'props': {}}
        nodes.append(cur)
        stack.append(cur)
    elif tok == 2:                    # FDT_END_NODE
        if stack:
            stack.pop()
        cur = stack[-1] if stack else None
    elif tok == 3:                    # FDT_PROP
        ln, nameoff = struct.unpack_from('>II', data, off)
        off += 8
        val = data[off:off + ln]
        off = (off + ln + 3) & ~3
        if cur is not None:
            cur['props'][name_at(nameoff)] = val
    elif tok == 4:
        off = (off + 7) & ~3
    elif tok == 9:
        break

def show(node, keys=None):
    p = node['props']
    path_bits = []
    print('=' * 70)
    print('path:', '/' + node['name'])
    for k, v in p.items():
        if keys and not any(s in k for s in keys):
            continue
        if len(v) and all(32 <= c < 127 for c in v):
            print('  %-28s %s' % (k, v.decode(errors='replace')))
        elif len(v) % 4 == 0 and len(v) <= 32:
            print('  %-28s %s' % (k, ' '.join(str(x) for x in struct.unpack('>%dI' % (len(v)//4), v))))
        else:
            print('  %-28s <%d bytes>' % (k, len(v)))

want_touch = ('touch', 'goodix', 'gt99', 'spi@99', 'focal', 'synaptics', 'touchscreen')
for n in nodes:
    nm = n['name']
    if any(w in nm for w in ('goodix', 'gt9966', 'touchscreen', 'focaltech')):
        show(n)
print('\n===== spi@990000 and its children =====')
spi_node = None
for n in nodes:
    if n['name'].startswith('spi@990000') or n['name'].startswith('spi@99'):
        show(n, keys=('compatible', 'reg', 'interrupts', 'pinctrl', 'status', 'clock', 'dma', 'spi'))
        spi_node = n
print('\n===== all nodes with "goodix" in name =====')
for n in nodes:
    if 'goodix' in n['name']:
        show(n)
print('\nnode count:', len(nodes))
