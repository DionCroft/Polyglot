import hashlib,json,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'recovery';out.mkdir(exist_ok=True)
archive=out/'LectureLive-Windows-ARM64-Recovery.zip'
files=[]
for folder in ['dist/LectureLive','app','scripts','docs','glossaries','offline_dependencies/wheels']:
 files.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='get-pip.py')
files.extend(root/name for name in ['README.md','STATUS.md','requirements-lock.txt','LectureLive.pyw','pytest.ini','tests/test_core.py','offline_dependencies/python-3.11.9-embed-arm64.zip'])
manifest={}
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
 for p in files:
  name=p.relative_to(root).as_posix();h=hashlib.sha256()
  with p.open('rb') as f:
   for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
  manifest[name]=h.hexdigest();z.write(p,name)
 z.writestr('RECOVERY_SHA256.json',json.dumps(manifest,indent=2))
(root/'recovery/RECOVERY_SHA256.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(str(archive),archive.stat().st_size,'bytes',len(files),'files',flush=True)
with zipfile.ZipFile(archive) as z:
 bad=z.testzip()
 if bad:raise RuntimeError('Recovery ZIP integrity failed: '+bad)
print('Recovery ZIP CRC integrity verified',flush=True)
