from pathlib import Path
import wave,time,json
from app.system.offline import enforce_offline
enforce_offline()
import numpy as np
from app.asr.qnn_whisper import QnnWhisper
from app.translation.opus_mt import OpusMT
root=Path.cwd()
with wave.open(str(root/'tests/fixtures/jfk.wav')) as f:
 print('wav',f.getparams(),flush=True); audio=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(np.float32)/32768
asr=QnnWhisper(root/'models/whisper/fast',True)
t=time.perf_counter();english=asr.transcribe(audio);dt=time.perf_counter()-t
print('ASR',repr(english),dt,flush=True)
mt=OpusMT(root/'models/translation/opus')
t=time.perf_counter();zh=mt.translate('The interrupt service routine must remain relatively short.');td=time.perf_counter()-t
print('MT',repr(zh),td,flush=True)
report={'audio_seconds':len(audio)/16000,'asr_seconds':dt,'rtf':dt/(len(audio)/16000),'english':english,'translation_seconds':td,'chinese':zh,'providers':[asr.encoder.get_providers(),asr.decoder.get_providers()],'profiles':[asr.encoder.end_profiling(),asr.decoder.end_profiling()]}
(root/'docs/evidence/first-inference.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
