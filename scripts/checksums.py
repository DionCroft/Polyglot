import argparse,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');p.add_argument('--recovery',action='store_true');args=p.parse_args()
manifest=root/('RECOVERY_SHA256.json' if args.recovery else 'offline_dependencies/SHA256SUMS.json')
def sha(path):
 digest=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):digest.update(chunk)
 return digest.hexdigest()
if args.verify:
 expected=json.loads(manifest.read_text());bad=[name for name,digest in expected.items() if not (root/name).is_file() or sha(root/name)!=digest]
 if bad:raise SystemExit('Checksum mismatch: '+', '.join(bad))
 print('Verified',len(expected),'files')
else:
 paths=[p for folder in ['models','offline_dependencies','dist/LectureLive'] for p in (root/folder).rglob('*') if p.is_file() and p!=manifest and p.suffix not in {'.partial','.zip'}]
 paths.extend((root/'offline_dependencies').glob('*.zip'))
 expected={str(p.relative_to(root)).replace('\\','/'):sha(p) for p in paths}
 manifest.write_text(json.dumps(expected,indent=2),encoding='utf-8');print('Hashed',len(expected),'files')
