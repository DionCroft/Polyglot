from pathlib import Path
import json,urllib.request,zipfile,concurrent.futures
root=Path.cwd()
jobs=[]
repo='onnx-community/whisper-base';rev=json.load(urllib.request.urlopen('https://huggingface.co/api/models/'+repo))['sha']
for f in ['encoder_model_quantized.onnx','decoder_model_quantized.onnx','decoder_with_past_model_quantized.onnx']:
 jobs.append((f'https://huggingface.co/{repo}/resolve/{rev}/onnx/{f}','models/whisper/fast/cpu/'+f))
d=json.load(urllib.request.urlopen('https://huggingface.co/qualcomm/Whisper-Small/raw/main/release_assets.json'))
a=d['precisions']['float']['chipset_assets']['qualcomm-snapdragon-x-elite']['precompiled_qnn_onnx']
jobs.append((a['download_url'],'offline_dependencies/whisper-small-qnn.zip'))
repo='openai/whisper-small';rev=json.load(urllib.request.urlopen('https://huggingface.co/api/models/'+repo))['sha']
for f in ['config.json','tokenizer.json','preprocessor_config.json','generation_config.json']:
 jobs.append((f'https://huggingface.co/{repo}/resolve/{rev}/{f}','models/whisper/balanced/'+f))
def get(j):
 u,f=j;p=root/f;p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists(): urllib.request.urlretrieve(u,p)
 print(f,p.stat().st_size,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(get,jobs))
zipfile.ZipFile(root/'offline_dependencies/whisper-small-qnn.zip').extractall(root/'models/whisper/balanced/qnn')
(root/'docs/evidence/additional-model-sources.json').write_text(json.dumps(jobs,indent=2))
