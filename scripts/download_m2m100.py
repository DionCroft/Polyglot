import urllib.request,json,pathlib,concurrent.futures
root=pathlib.Path.cwd();repo='Xenova/m2m100_418M';d=json.load(urllib.request.urlopen('https://huggingface.co/api/models/'+repo));rev=d['sha'];print(rev,flush=True)
files=['config.json','generation_config.json','tokenizer.json','vocab.json','sentencepiece.bpe.model','tokenizer_config.json','README.md','onnx/encoder_model_quantized.onnx','onnx/decoder_model_quantized.onnx','onnx/decoder_with_past_model_quantized.onnx']
known={x['rfilename'] for x in d['siblings']};files=[f for f in files if f in known]
jobs=[(f'https://huggingface.co/{repo}/resolve/{rev}/{f}',root/'models/translation/m2m100'/f) for f in files]
def get(job):
 u,p=job;p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():
  tmp=p.with_suffix(p.suffix+'.partial');urllib.request.urlretrieve(u,tmp);tmp.replace(p)
 print(p.name,p.stat().st_size,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(get,jobs))
(root/'docs/evidence/m2m100-sources.json').write_text(json.dumps([(u,str(p.relative_to(root))) for u,p in jobs],indent=2))
