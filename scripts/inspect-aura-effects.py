"""Extract named particle candidates from a user-supplied decrypted CIA.
Usage: python inspect-aura-effects.py GAME.cia OUTPUT_DIRECTORY
Names alone do not establish which effect is used for good/evil/solid-color auras.
"""
import hashlib, io, json, re, struct, sys, zipfile
from pathlib import Path

def inspect(path, output):
    output.mkdir(parents=True, exist_ok=True)
    with path.open('rb') as f:
        def read(pos, n):
            f.seek(pos)
            return f.read(n)
        header_size, _, _, cert, ticket, tmd, _, _ = struct.unpack('<IHHIIIIQ', read(0, 32))
        align = lambda n: (n + 63) // 64 * 64
        ncch = sum(map(align, [header_size, cert, ticket, tmd]))
        if read(ncch + 0x100, 4) != b'NCCH':
            raise ValueError('CIA content is not decrypted NCCH')
        romfs = ncch + struct.unpack('<I', read(ncch + 0x1B0, 4))[0] * 512
        if read(romfs, 4) != b'IVFC':
            raise ValueError('RomFS is not decrypted')
        base = romfs + 0x1000
        h = struct.unpack('<10I', read(base, 40))
        dirs, files, data = base + h[3], base + h[7], base + h[9]
        inventory = []
        def walk(off, parent):
            _, _, child, file, _, length = struct.unpack('<6I', read(dirs + off, 24))
            name = read(dirs + off + 24, length).decode('utf-16le')
            parent = parent + '/' + name if name else parent
            while file != 0xFFFFFFFF:
                _, sibling, pos, size, _, length = struct.unpack('<IIQQII', read(files + file, 32))
                name = read(files + file + 32, length).decode('utf-16le')
                if not parent and size >= 24:
                    archive = read(data + pos, size)
                    if struct.unpack_from('<I', archive)[0] == 10:
                        count = struct.unpack_from('<I', archive, 16)[0]
                        if 24 + count * 28 <= size:
                            for i in range(count):
                                row = struct.unpack_from('<7I', archive, 24 + 28 * i)
                                packed = archive[row[3]:row[3] + row[2]]
                                if not packed.startswith(b'PK\x03\x04'):
                                    continue
                                with zipfile.ZipFile(io.BytesIO(packed)) as z:
                                    for item in z.namelist():
                                        if re.search(r'(aura|fx_cat_.*(?:rare|glow)).*\.ptcl$', item, re.I):
                                            raw = z.read(item)
                                            target = output / Path(item).name
                                            target.write_bytes(raw)
                                            inventory.append({'archive': name, 'file': target.name, 'sha256': hashlib.sha256(raw).hexdigest(), 'magic': raw[:4].decode('ascii', errors='replace'), 'version': struct.unpack_from('<I', raw, 4)[0]})
                file = sibling
            while child != 0xFFFFFFFF:
                sibling = struct.unpack('<I', read(dirs + child + 4, 4))[0]
                walk(child, parent)
                child = sibling
        walk(0, '')
    (output / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print('Extracted', len(inventory), 'candidate effects; category mapping is unverified.')

if __name__ == '__main__':
    inspect(Path(sys.argv[1]), Path(sys.argv[2]))
