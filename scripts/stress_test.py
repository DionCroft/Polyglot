import argparse,json,time,wave,threading
from pathlib import Path
from app.system.offline import enforce_offline
enforce_offline()
import psutil
from app.config.settings import Settings
from app.pipeline import Pipeline
parser=argparse.ArgumentParser();parser.add_argument('--seconds',type=int,default=600);args=parser.parse_args()
root=Path(__file__).resolve().parents[1];target=root/'tests/artifacts/stress.wav';target.parent.mkdir(parents=True,exist_ok=True)
with wave.open(str(root/'tests/fixtures/technical.wav')) as f:source=f.readframes(f.getnframes())
with wave.open(str(target),'wb') as f:
 f.setnchannels(1);f.setsampwidth(2);f.setframerate(16000)
 remaining=args.seconds*16000*2
 while remaining>0:
  chunk=source[:remaining];f.writeframesraw(chunk);remaining-=len(chunk)
counts={'final_english':0,'bilingual':0};warnings=[];samples=[]
def emit(kind,value):
 if kind=='caption' and value.final:counts['bilingual' if value.chinese else 'final_english']+=1
 if kind=='warning':warnings.append(str(value))
p=Pipeline(root,root/'tests/artifacts/stress-data',Settings(profile='balanced'),emit,wav=target)
p.start();process=psutil.Process();start=time.monotonic();next_sample=start
while p.source and p.source.thread.is_alive():
 now=time.monotonic()
 if now>=next_sample:
  samples.append({'elapsed':now-start,'rss_mb':process.memory_info().rss/1048576,'threads':process.num_threads(),'cpu_percent':process.cpu_percent(),**p.diagnostics(),'inet_connections':len(process.net_connections(kind='inet'))})
  (root/f'docs/evidence/stress-{args.seconds}s-progress.json').write_text(json.dumps({'counts':counts,'samples':samples,'warnings':warnings},indent=2),encoding='utf-8')
  next_sample=now+10
 time.sleep(.2)
time.sleep(2);p.close()
report={'duration_seconds':time.monotonic()-start,'counts':counts,'samples':samples,'warnings':warnings,'workers_alive':[t.name for t in p.threads if t.is_alive()]}
(root/f'docs/evidence/stress-{args.seconds}s.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'duration':report['duration_seconds'],'counts':counts,'rss_first_mb':samples[0]['rss_mb'],'rss_last_mb':samples[-1]['rss_mb'],'workers_alive':report['workers_alive']}),flush=True)
assert counts['bilingual']>=max(1,args.seconds//90)
assert not report['workers_alive']
