import time,platform
from pathlib import Path
from app.system.offline import enforce_offline
enforce_offline()
import numpy as np
import onnxruntime as ort
from app.system.inference import session,qnn_devices
root=Path(__file__).resolve().parents[1]
print(platform.machine(),ort.__version__,flush=True)
print([(d.ep_name,str(d.device)) for d in qnn_devices()],flush=True)
for name in ["encoder","decoder"]:
    p=next((root/"models/whisper/fast/qnn").rglob(name+".onnx"))
    t=time.perf_counter(); s=session(p,True,True)
    print(name,"loaded",time.perf_counter()-t,s.get_providers(),flush=True)
    print([(i.name,i.shape,i.type) for i in s.get_inputs()],flush=True)
    print([(i.name,i.shape) for i in s.get_outputs()],flush=True)
    if name=="encoder":
        t=time.perf_counter();s.run(None,{s.get_inputs()[0].name:np.zeros((1,80,3000),dtype=np.float16)})
        print("encoder seconds",time.perf_counter()-t,flush=True)
    print("profile",s.end_profiling(),flush=True)
