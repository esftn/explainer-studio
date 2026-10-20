"""Split a big file into ≤14 MB parts for transfer tools with a size cap, with md5 to verify after re-joining.
usage: python split_deliver.py <file> [--mb 14]
Re-join on the destination:  cat <name>.part_* > <name>   then compare  md5 (mac: md5 -q, linux: md5sum)."""
import argparse, hashlib, pathlib
ap = argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--mb', type=float, default=14)
a = ap.parse_args(); f = pathlib.Path(a.file); data = f.read_bytes(); n = int(a.mb * 1024 * 1024)
md5 = hashlib.md5(data).hexdigest(); parts = []
for i in range(0, len(data), n):
    p = f.with_name(f'{f.name}.part_{i // n:02d}'); p.write_bytes(data[i:i + n]); parts.append(p.name)
f.with_name(f.name + '.md5').write_text(md5 + '\n')
print(f'{len(parts)} parts, md5 {md5}\njoin: cat {f.name}.part_* > {f.name}')
