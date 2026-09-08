from pathlib import Path
import json,time,wave,re
from app.system.offline import enforce_offline
enforce_offline()
import numpy as np
from app.asr.qnn_whisper import QnnWhisper
from app.translation.opus_mt import OpusMT
from app.captions.glossary import Glossary
root=Path(__file__).resolve().parents[1]
cases=[r for r in json.loads((root/'docs/evidence/translation-comparison.json').read_text(encoding='utf-8')) if r['backend']=='opus']
asr=QnnWhisper(root/'models/whisper/balanced');mt=OpusMT(root/'models/translation/opus');rows=[]
for i,case in enumerate(cases):
 with wave.open(str(root/f'tests/fixtures/technical-{i}.wav')) as f:
  assert f.getframerate()==16000 and f.getnchannels()==1 and f.getsampwidth()==2
  audio=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(np.float32)/32768
 t=time.perf_counter();english=asr.transcribe(audio);asr_time=time.perf_counter()-t
 glossary=Glossary(root/'glossaries'/('robotics.json' if i==6 else 'artificial_intelligence.json' if i==7 else 'embedded_systems.json'))
 raw_english=english;english=glossary.english(english)
 t=time.perf_counter();chinese=glossary.chinese(english,mt.translate(english));mt_time=time.perf_counter()-t
 expected=re.findall(r'[a-z0-9]+',case['english'].lower());actual=re.findall(r'[a-z0-9]+',english.lower());dp=list(range(len(actual)+1))
 for row,word in enumerate(expected,1):
  new=[row]
  for col,other in enumerate(actual,1):new.append(min(new[-1]+1,dp[col]+1,dp[col-1]+(word!=other)))
  dp=new
 result={'reference_english':case['english'],'raw_asr':raw_english,'recognized_english':english,'chinese':chinese,'word_error_rate':dp[-1]/max(1,len(expected)),'audio_seconds':len(audio)/16000,'asr_seconds':asr_time,'translation_seconds':mt_time}
 rows.append(result);print(json.dumps(result,ensure_ascii=False),flush=True)
(root/'docs/evidence/technical-benchmark.json').write_text(json.dumps({'source':'Locally synthesized Windows speech, not a real lecturer accuracy benchmark','results':rows},ensure_ascii=False,indent=2),encoding='utf-8')
