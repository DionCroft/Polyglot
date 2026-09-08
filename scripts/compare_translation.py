from pathlib import Path
import time,json
from app.system.offline import enforce_offline
enforce_offline()
from app.translation.m2m100 import M2M100
from app.translation.opus_mt import OpusMT
root=Path.cwd()
texts=['The ESP32 communicates with the sensor using the I-squared-C protocol.','Pulse-width modulation changes the average voltage applied to the motor.','An interrupt service routine should execute as quickly as possible.','The FreeRTOS scheduler performs a context switch between tasks.','The FPGA design is written in VHDL and synthesised into logic resources.','The MOSFET is being driven using a pulse-width-modulated signal.','The robot uses an ultrasonic sensor to estimate its distance from an obstacle.','A convolutional neural network can perform image classification at the edge.']
results=[]
for kind,cls,folder in [('opus',OpusMT,'opus'),('m2m100',M2M100,'m2m100')]:
 model=cls(root/'models/translation'/folder)
 for text in texts:
  start=time.perf_counter();translation=model.translate(text);elapsed=time.perf_counter()-start
  print(kind,round(elapsed,3),text,translation,flush=True)
  results.append({'backend':kind,'english':text,'chinese':translation,'seconds':elapsed})
 del model
(root/'docs/evidence/translation-comparison.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
