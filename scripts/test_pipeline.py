from pathlib import Path
import time,json
from app.system.offline import enforce_offline
enforce_offline()
from app.config.settings import Settings
from app.pipeline import Pipeline
root=Path(__file__).resolve().parents[1]
events=[]
def emit(kind,value):
 if kind=='caption':
  print('FINAL' if value.final else 'PARTIAL',value.english,value.chinese,flush=True)
  if value.final:events.append(value.__dict__)
 else:print(kind,value,flush=True)
p=Pipeline(root,root/'tests/artifacts',Settings(microphone=9,profile='balanced'),emit,wav=root/'tests/fixtures/technical.wav')
p.start()
while p.source and p.source.thread.is_alive():time.sleep(.2)
limit=time.monotonic()+10
while (len(p.phrases) or p.translation.qsize()) and time.monotonic()<limit:time.sleep(.1)
time.sleep(1)
p.close()
(root/'docs/evidence/pipeline.json').write_text(json.dumps({'events':events,'metrics':p.diagnostics(),'worker_threads_remaining':[t.name for t in p.threads if t.is_alive()]},ensure_ascii=False,indent=2),encoding='utf-8')
assert any(e['chinese'] for e in events),'No bilingual captions produced'
assert not any(t.is_alive() for t in p.threads)
