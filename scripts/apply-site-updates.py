"""Apply small, hash-checked updates to the GitHub Pages base archive.

Usage: python apply_pages_updates.py SITE_DIRECTORY MANIFEST
The manifest is generated from the exact previous public ZIP and a checked build.
"""
import base64,hashlib,json,subprocess,sys,zlib
from pathlib import Path

def apply(root,manifest):
    data=json.loads(manifest.read_text())
    if data['schema']!='chetsupro-pages-updates/1':raise ValueError('Unknown update manifest')
    for update in data['changes']:
        name=update['path']
        if name not in ('basic.html','birth.html','geki.html'):raise ValueError('Unexpected update path')
        target=root/name;digest=hashlib.sha256(target.read_bytes()).hexdigest()
        if digest==update['after']:continue
        if digest!=update['before']:raise ValueError('Base ZIP changed: regenerate or remove site-updates.json before publishing '+name)
        patch=zlib.decompress(base64.b64decode(update['patch_zlib_base64']))
        subprocess.run(['patch','--batch','--forward','--strip=1','--directory',str(root)],input=patch,check=True,capture_output=True)
        if hashlib.sha256(target.read_bytes()).hexdigest()!=update['after']:raise ValueError('Updated file did not match the checked build: '+name)
    print('Applied checked site updates: '+data['version'])

if __name__=='__main__':apply(Path(sys.argv[1]),Path(sys.argv[2]))
