from pathlib import Path
import urllib.request,json,zipfile,concurrent.futures,hashlib
root=Path.cwd()
def get(url,path):
 path=root/path; path.parent.mkdir(parents=True,exist_ok=True)
 if not path.exists():
  tmp=path.with_suffix(path.suffix+'.partial'); urllib.request.urlretrieve(url,tmp); tmp.replace(path)
 print(str(path.relative_to(root)),path.stat().st_size,flush=True)
 return path
asset=json.loads((root/'docs/evidence/qualcomm-release-assets.json').read_text())['precisions']['float']['chipset_assets']['qualcomm-snapdragon-x-elite']['precompiled_qnn_onnx']
jobs=[(asset['download_url'],'offline_dependencies/whisper-base-qnn.zip')]
for repo,folder,files in [('openai/whisper-base','models/whisper/fast',['tokenizer.json','config.json','preprocessor_config.json','generation_config.json']),('onnx-community/opus-mt-en-zh','models/translation/opus',['config.json','generation_config.json','tokenizer.json','tokenizer_config.json','vocab.json','source.spm','target.spm','onnx/encoder_model_quantized.onnx','onnx/decoder_model_quantized.onnx','onnx/decoder_with_past_model_quantized.onnx','README.md'])]:
 rev=json.load(urllib.request.urlopen('https://huggingface.co/api/models/'+repo))['sha']
 for f in files: jobs.append(('https://huggingface.co/'+repo+'/resolve/'+rev+'/'+f,folder+'/'+f))
(root/'docs/evidence/download-sources.json').write_text(json.dumps(jobs,indent=2))
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
 for f in pool.map(lambda j:get(*j),jobs): pass
z=zipfile.ZipFile(root/'offline_dependencies/whisper-base-qnn.zip');print(z.namelist());z.extractall(root/'models/whisper/fast/qnn')
get('https://raw.githubusercontent.com/ggml-org/whisper.cpp/master/samples/jfk.wav','tests/fixtures/jfk.wav')
