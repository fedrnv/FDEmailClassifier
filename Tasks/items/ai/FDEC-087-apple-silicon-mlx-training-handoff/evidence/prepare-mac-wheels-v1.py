"""Cross-download/inspect Mac tooling only. No Apple execution or model weights."""
from email.parser import BytesParser
import hashlib,json
from pathlib import Path
import subprocess,sys,urllib.request,zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
destination=ROOT/'training/data/mlx-mac-wheels-v1'
if destination.exists():raise ValueError('append_only_mac_wheel_acquisition')
destination.mkdir(parents=True)
pins={'mlx':'0.32.4','mlx-metal':'0.32.4','mlx-lm':'0.32.2','numpy':'2.5.5','transformers':'5.23.0','safetensors':'0.8.0','pyarrow':'26.0.1','sentencepiece':'0.2.3','PyYAML':'6.0.3'}
result=subprocess.run([sys.executable,'-m','pip','download','--only-binary=:all:','--platform','macosx_15_0_arm64','--python-version','314','--implementation','cp','--abi','cp314','--dest',str(destination),*[name+'=='+version for name,version in pins.items()]],capture_output=True)
(destination/'acquisition.log').write_bytes(result.stdout+b'\n'+result.stderr)
if result.returncode:raise ValueError('cross_platform_download_failed')
rows=[]
old=ROOT/'Tasks/items/ai/FDEC-019-model-export-and-provenance/evidence'
supplements={('tokenizers','0.23.3'):next(row['versioned_license_supplement'] for row in json.loads((old/'model-wheel-observations-v2.json').read_text())['wheels'] if row['name']=='tokenizers'),('sentencepiece','0.2.3'):json.loads((old/'sentencepiece-observation-v2.json').read_text())['license_supplement']}
for path in sorted(destination.glob('*.whl')):
    with zipfile.ZipFile(path) as archive:
        meta=BytesParser().parsebytes(archive.read(next(n for n in archive.namelist() if n.endswith('.dist-info/METADATA'))))
        name,version=meta['Name'],meta['Version'];url=f'https://pypi.org/pypi/{name}/{version}/json'
        with urllib.request.urlopen(url,timeout=30) as response:public=json.load(response)
        row=next(item for item in public['urls'] if item['filename']==path.name)
        sha=hashlib.sha256(path.read_bytes()).hexdigest()
        if sha!=row['digests']['sha256'] or path.stat().st_size!=row['size']:raise ValueError('mac_wheel_hash_mismatch')
        licenses=[]
        for entry in archive.namelist():
            if '.dist-info/' in entry and any(word in entry.lower() for word in ('license','copying','notice')) and not entry.endswith('/'):
                raw=archive.read(entry);licenses.append(dict(path=entry,sha256=hashlib.sha256(raw).hexdigest(),prefix=raw.decode(errors='replace')[:350]))
        supplement=supplements.get((name,version)) if not licenses else None
        if not licenses and not supplement:raise ValueError('mac_wheel_license_unresolved:'+name)
        rows.append(dict(name=name,version=version,filename=path.name,url=row['url'],sha256=sha,size=row['size'],license=meta.get('License-Expression') or meta.get('License'),licenses=licenses,versioned_license_supplement=supplement))
with (HERE/'mac-wheel-observations-v1.json').open('x',encoding='utf-8') as out:out.write(json.dumps(dict(schema='fdec-mac-wheel-observations/v1',platform='CPython-3.14-macOS-15+-arm64',wheels=rows,installed=False,apple_execution=False,model_tensors_downloaded=False,redistribution_approved=False),indent=2)+'\n')
print(json.dumps(dict(wheels=len(rows),installed=False,apple_execution=False,model_tensors_downloaded=False)))
