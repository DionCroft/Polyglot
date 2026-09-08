from pathlib import Path
from unittest.mock import patch
import time,json
from app.system.offline import enforce_offline
enforce_offline()
from app.pipeline import Pipeline
from app.config.settings import Settings
root=Path(__file__).resolve().parents[1];events=[]
def emit(kind,value):events.append((kind,value))
with patch('app.asr.qnn_whisper.QnnWhisper.__init__',side_effect=RuntimeError('Simulated NPU unavailable')),patch('app.translation.opus_mt.OpusMT.__init__',side_effect=FileNotFoundError('Simulated missing local translation model')):
 p=Pipeline(root,root/'tests/artifacts/failure-data',Settings(profile='balanced'),emit,wav=root/'tests/fixtures/technical.wav')
 try:
  p.start();limit=time.monotonic()+15
  while time.monotonic()<limit and not any(k=='caption' and v.final for k,v in events):time.sleep(.05)
 finally:p.close()
assert any(k=='caption' and v.final for k,v in events)
assert 'CPU' in p.asr.name
assert any(k=='warning' and 'Translation' in v for k,v in events)
assert not any(t.is_alive() for t in p.threads)
# Device-open failure never crashes or leaves workers after shutdown.
events2=[]
with patch('app.audio.capture.Microphone.start',side_effect=RuntimeError('Microphone disconnected')):
 q=Pipeline(root,root/'tests/artifacts/failure-data',Settings(save_transcripts=False),lambda k,v:events2.append((k,v)))
 q.start();assert q.paused.is_set();q.close()
assert not any(t.is_alive() for t in q.threads)
(root/'docs/evidence/failure-tests.json').write_text(json.dumps({'npu_missing_cpu_recovery':True,'translation_missing_english_continues':True,'microphone_open_failure_clean_shutdown':True,'physical_unplug_test':False},indent=2))
print('Failure tests passed: CPU recovery, missing translation, microphone open failure')
