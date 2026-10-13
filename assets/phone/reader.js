"use strict";
const $ = id => document.getElementById(id);
const reader=$('reader'), entries=$('entries');
let rows=[], version=-1, follow=true, busy=false, requestId=0, active=null, adjusting=false;
let earlier=false, later=false, query='', timer=null, font=22;
try { $('view').value=localStorage.getItem('lecturelive-view')||'both'; font=Number(localStorage.getItem('lecturelive-size'))||22; } catch (_) {}
font=Math.max(16,Math.min(34,font));
function preferences() {
  document.documentElement.style.setProperty('--reading-size',font+'px');
  $('download').href='transcript.txt?view='+$('view').value;
  try {localStorage.setItem('lecturelive-view',$('view').value); localStorage.setItem('lecturelive-size',font);} catch (_) {}
}
function anchor() {
  const top=reader.getBoundingClientRect().top;
  const node=Array.from(entries.children).find(n=>n.getBoundingClientRect().bottom>top+3);
  return node?{id:node.dataset.id,offset:node.getBoundingClientRect().top-top}:null;
}
function textFor(c) {
  if(c.kind!=='caption') return (c.kind==='gap'?'[Audio lost] ':'[Not transcribed] ')+c.reason;
  const output=[];
  for(const [lang,label,key] of [['en','English','english'],['zh','简体中文','chinese']]) {
    if($('view').value!=='both' && $('view').value!==lang) continue;
    const value=c[key] || (c.translation_status==='unavailable'?'[Translation unavailable]':'[Translation pending]');
    output.push(label+(c.source_language===lang?' · spoken: ':' · translation: ')+value);
  }
  return output.join('\n');
}
async function copy(text) {
  let ok=false;
  try {if(navigator.clipboard && window.isSecureContext) {await navigator.clipboard.writeText(text);ok=true;}} catch (_) {}
  if(!ok) {
    const box=document.createElement('textarea');box.value=text;box.setAttribute('readonly','');
    box.style.position='fixed';box.style.opacity='0';document.body.append(box);box.select();box.setSelectionRange(0,box.value.length);
    try {ok=document.execCommand('copy');} catch (_) {} box.remove();
  }
  $('notice').textContent=ok?'Copied.':'Copy unavailable here; select text or download the transcript.';
  return ok;
}
function card(c, node) {
  if(!node) {
    node=document.createElement('article');node.className='entry';node.dataset.id=String(c.identifier);
    const head=document.createElement('div');head.className='entry-head';
    const time=document.createElement('time');head.append(time);
    const button=document.createElement('button');button.textContent='Copy';button.setAttribute('aria-label','Copy this caption');
    button.addEventListener('click',async()=>{
      const ok=await copy(textFor(node.caption));button.textContent=ok?'Copied':'Copy failed';
      setTimeout(()=>{button.textContent='Copy';},2000);
    });head.append(button);node.append(head);
    for(const lang of ['en','zh']) {
      const block=document.createElement('section');block.className=lang;block.lang=lang==='zh'?'zh-Hans':'en';
      const label=document.createElement('div');label.className='language';block.append(label);
      const text=document.createElement('p');text.className='text';block.append(text);node.append(block);
    }
    const message=document.createElement('p');message.className='message';node.append(message);
  }
  node.caption=c;
  const set=(element,value)=>{if(element.textContent!==value)element.textContent=value;};
  const seconds=Math.max(0,Math.floor(c.start));
  set(node.querySelector('time'),[Math.floor(seconds/3600),Math.floor(seconds/60)%60,seconds%60].map(n=>String(n).padStart(2,'0')).join(':'));
  for(const [lang,name,key] of [['en','English','english'],['zh','简体中文','chinese']]) {
    const block=node.querySelector('.'+lang);
    block.hidden=c.kind!=='caption' || ($('view').value!=='both' && $('view').value!==lang);
    set(block.querySelector('.language'),name+(c.source_language===lang?' · spoken':' · translation'));
    const text=block.querySelector('.text');
    set(text,c[key] || (c.translation_status==='unavailable'?'Translation unavailable / 翻译不可用':'Translation pending… / 等待翻译…'));
    text.classList.toggle('pending',!c[key]);
  }
  const message=node.querySelector('.message');message.hidden=c.kind==='caption';
  set(message,c.kind==='caption'?'':textFor(c));
  return node;
}
function render(saved=anchor()) {
  adjusting=true;
  const existing=new Map(Array.from(entries.children).map(n=>[n.dataset.id,n]));
  const keep=new Set(rows.map(c=>String(c.identifier)));
  for(const node of Array.from(entries.children)) if(!keep.has(node.dataset.id)) node.remove();
  rows.forEach((c,index)=>{
    const node=card(c,existing.get(String(c.identifier)));
    if(entries.children[index]!==node) entries.insertBefore(node,entries.children[index]||null);
  });
  $('older').hidden=!earlier; $('newer').hidden=!later;
  $('empty').hidden=rows.length>0;
  $('empty').textContent=query?'No matches yet. Search checks the whole shared lecture.':'Waiting for the lecturer’s first completed sentence…';
  $('live').hidden=follow && !query;
  if(follow && !query) reader.scrollTop=reader.scrollHeight;
  else if(saved) {
    const node=entries.querySelector('[data-id="'+saved.id+'"]');
    if(node) reader.scrollTop+=node.getBoundingClientRect().top-reader.getBoundingClientRect().top-saved.offset;
  }
  requestAnimationFrame(()=>requestAnimationFrame(()=>{adjusting=false;}));
}
async function load(mode='refresh',force=false) {
  if(busy && !force)return;
  if(active)active.abort();
  const id=++requestId, controller=new AbortController();active=controller;busy=true;
  const timeout=setTimeout(()=>controller.abort(),8000);
  const requestFollow=follow;const params=new URLSearchParams({limit:String(mode==='older'||mode==='newer'?40:120)});
  if(query)params.set('q',query);
  if(mode==='older' && rows.length)params.set('before',rows[0].identifier);
  else if(mode==='newer' && rows.length)params.set('after',rows[rows.length-1].identifier);
  else if(!follow && mode!=='reset' && rows.length)params.set('start',rows[0].identifier);
  if(mode==='refresh')params.set('version',String(Math.max(0,version)));
  try {
    const response=await fetch('api/page?'+params,{cache:'no-store',signal:controller.signal});
    if(!response.ok)throw Error('Sharing unavailable');
    const data=await response.json();if(id!==requestId)return;
    $('connection').textContent='Connected · local network';$('connection').classList.remove('reconnecting');
    $('lecture-state').textContent=data.state;
    $('coverage').textContent=data.coverage+' · automated captions may contain errors.';
    if(data.unchanged)return;
    if(mode==='refresh' && requestFollow && !follow)return;
    const saved=mode==='reset'?null:anchor();
    // Paging keeps some existing rows: force one refresh to catch late updates to them.
    version=(mode==='older'||mode==='newer')?-1:data.revision;
    if(mode==='older') {rows=[...data.entries,...rows].slice(0,120);earlier=data.more_before;later=true;}
    else if(mode==='newer') {rows=[...rows,...data.entries].slice(-120);later=data.more_after;earlier=true;}
    else {rows=data.entries;earlier=data.more_before;later=data.more_after;}
    // IDs are stable; late translations replace their own row, never append copies.
    rows=Array.from(new Map(rows.map(c=>[c.identifier,c])).values()).sort((a,b)=>a.identifier-b.identifier);
    $('count').textContent=(query?'Search results · ': '')+rows.length+' shown / '+data.count+' shared entries';
    render(saved);
    if(mode==='reset' && !follow)reader.scrollTop=0;
  } catch (_) {
    if(id!==requestId)return;
    $('connection').textContent='Reconnecting… Sharing may have stopped. Showing received captions.';
    $('connection').classList.add('reconnecting');
  } finally {clearTimeout(timeout);if(id===requestId){busy=false;active=null;}}
}
reader.addEventListener('scroll',()=>{
  if(adjusting)return;
  const bottom=reader.scrollHeight-reader.clientHeight-reader.scrollTop;
  if(bottom>70)follow=false;
  else if(!later && !query)follow=true;
  $('live').hidden=follow && !query;
  if(!follow && reader.scrollTop<100 && earlier)load('older');
  else if(bottom<80 && later)load('newer');
},{passive:true});
$('older').onclick=()=>{follow=false;load('older');};
$('newer').onclick=()=>{follow=false;load('newer');};
$('live').onclick=()=>{clearTimeout(timer);follow=true;query='';$('search').value='';version=-1;load('reset',true);};
$('search').addEventListener('input',()=>{
  clearTimeout(timer);
  timer=setTimeout(()=>{query=$('search').value.trim();follow=!query;version=-1;rows=[];load('reset',true);},300);
});
$('view').onchange=()=>{const saved=anchor();preferences();render(saved);};
$('smaller').onclick=()=>{const saved=anchor();font=Math.max(16,font-2);preferences();render(saved);};
$('larger').onclick=()=>{const saved=anchor();font=Math.min(34,font+2);preferences();render(saved);};
$('copy').onclick=()=>copy(rows.map(textFor).join('\n\n'));
window.addEventListener('online',()=>load('refresh'));
preferences();load('reset');setInterval(()=>load('refresh'),1500);
