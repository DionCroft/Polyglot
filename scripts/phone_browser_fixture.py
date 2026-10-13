"""Synthetic browser fixtures only; not speech accuracy evidence."""
import sys
from dataclasses import replace
from pathlib import Path
from app.captions.state import Caption
from app.sharing.history import Database

mode,path=sys.argv[1:3]
with Database(Path(path),write=True) as db:
    if mode=='seed':
        for i in range(1,10001):
            en=f'Turn {i}. The project risk register records probability, impact and the response owner.'
            zh=f'第{i}段。项目风险登记册记录概率、影响和应对负责人。'
            if i==1: en+=' needle-first'
            if i%1000==0: en+=' A longer technical explanation. '*50; zh+='这是一段较长的技术说明。'*70
            if i==9980: en+=" <img src='https://example.invalid/never-fetch'> <script>window.injected=true</script>"
            c=Caption(i,i*3,i*3+2,en,zh,True,source_language='zh' if i%2 else 'en',translation_status='complete')
            if i==9920:c=replace(c,chinese='',translation_status='pending')
            db.put('english' if i==9920 else 'pair',c)
        db.set_meta('state','Listening')
    elif mode=='late':
        row=db.conn.execute('SELECT payload FROM entries WHERE identifier=9920').fetchone()
        import json
        c=json.loads(row[0]);c['chinese']='延迟的完整译文。'*400;c['translation_status']='complete';c.pop('kind')
        db.put('pair',c)
        db.put('pair',Caption(10001,30003,30005,'Latest after delay','延迟后最新内容',True,translation_status='complete'))
    elif mode=='reconnect':
        db.put('pair',Caption(10002,30006,30008,'New after reconnect','重新连接后的内容',True,translation_status='complete'))
    else: raise ValueError(mode)
