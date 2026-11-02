"""Download source tables with snapshot hash verification; no external dependencies."""
import hashlib
import json
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parent
target = root / 'data'
target.mkdir(exist_ok=True)
for name, source in json.loads((root/'sources.json').read_text()).items():
    path = target/name
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == source['sha256']:
        print('Verified local:', name)
        continue
    with urllib.request.urlopen(source['url'], timeout=60) as response:
        content = response.read()
    if hashlib.sha256(content).hexdigest() != source['sha256']:
        raise RuntimeError(f'{name}: upstream changed; review the new data before updating sources.json')
    json.loads(content)
    temporary = target/(name+'.tmp')
    temporary.write_bytes(content)
    temporary.replace(path)
    print('Downloaded and verified:', name)
