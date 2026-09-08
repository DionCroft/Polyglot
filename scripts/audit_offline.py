import ast,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
forbidden={'requests','urllib','http','httpx','openai','azure','google','huggingface_hub','socket','websockets','aiohttp'}
violations=[]
for path in (root/'app').rglob('*.py'):
 for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
  names=[alias.name for alias in node.names] if isinstance(node,ast.Import) else [node.module or ''] if isinstance(node,ast.ImportFrom) else []
  for name in names:
   if name.split('.')[0] in forbidden:violations.append({'file':str(path.relative_to(root)),'line':node.lineno,'import':name})
report={'runtime_python_files':len(list((root/'app').rglob('*.py'))),'forbidden_network_imports':violations,'ort_telemetry_disabled':'disable_telemetry_events()' in (root/'app/system/inference.py').read_text(),'native_packet_trace':'pending; not proven by static audit'}
(root/'docs/evidence/offline-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
assert not violations
