/* Browser emulation on Windows; does not certify physical phones or classroom Wi-Fi. */
const fs=require('fs'),path=require('path'),{spawn,execFileSync}=require('child_process');
const {chromium,devices}=require('../build/phone-browser/node_modules/playwright');
const root=path.resolve(__dirname,'..'),art=path.join(root,'tests/artifacts/phone-browser');
fs.mkdirSync(art,{recursive:true});
const python=path.join(root,'runtime/python.exe'),db=path.join(art,'browser-'+Date.now()+'.sqlite');
const status=db+'.json',token='browser-test-'+require('crypto').randomBytes(24).toString('hex');
function fixture(mode){execFileSync(python,['-X','utf8','-m','scripts.phone_browser_fixture',mode,db],{cwd:root,stdio:'pipe'});}
const wait=ms=>new Promise(r=>setTimeout(r,ms));
function assert(value,message){if(!value)throw Error(message);}
(async()=>{
  fixture('seed');
  const helper=spawn(python,['-m','app.main','--student-server',db,'127.0.0.1',status],{cwd:root,env:{...process.env,LECTURELIVE_SHARE_KEY:token},stdio:['pipe','pipe','pipe']});
  let errors='';helper.stderr.on('data',s=>errors+=s);
  let browser;
  const result={passed:false,physical_phones_tested:false,classroom_wifi_tested:false,engine:'Microsoft Edge, Chromium mobile emulation',checks:[]};
  try{
    for(let n=0;n<200&&!fs.existsSync(status);n++)await wait(50);
    assert(fs.existsSync(status),'Server startup timed out '+errors);
    const state=JSON.parse(fs.readFileSync(status,'utf8'));assert(state.ready,JSON.stringify(state));
    const url=`http://127.0.0.1:${state.port}/s/${token}/`;
    browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--disable-background-networking','--no-first-run']});
    const context=await browser.newContext({...devices['iPhone 13'],acceptDownloads:true});
    const page=await context.newPage(),outside=[],jsErrors=[];
    page.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1:'))outside.push(r.url());});
    page.on('pageerror',e=>jsErrors.push(e.message));
    await page.goto(url);await page.waitForSelector('.entry[data-id="10000"]');
    assert(await page.locator('.entry').count()===120,'Client history must be bounded');
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile horizontal overflow');
    result.checks.push('10,000 entries available; only 120 mounted; mobile layout fits');
    await page.locator('.entry[data-id="9950"]').scrollIntoViewIfNeeded();await wait(200);
    const getAnchor=()=>page.evaluate(()=>{const r=document.getElementById('reader'),top=r.getBoundingClientRect().top;const n=[...document.querySelectorAll('.entry')].find(n=>n.getBoundingClientRect().bottom>top+3);return {id:n.dataset.id,offset:n.getBoundingClientRect().top-top};});
    const before=await getAnchor();
    fixture('late');await page.waitForFunction(()=>document.querySelector('[data-id="9920"] .zh .text')?.textContent.includes('延迟的完整译文'));await wait(100);
    const after=await getAnchor();assert(before.id===after.id&&Math.abs(before.offset-after.offset)<3,'Delayed translation moved reader: '+JSON.stringify({before,after}));
    assert(await page.locator('[data-id="9920"]').count()===1,'Duplicate delayed translation');
    assert(await page.locator('#live').isVisible(),'Back to live missing');
    result.checks.push('Late long translation updates original row; reading anchor unchanged');
    await page.locator('#live').click();await page.waitForSelector('[data-id="10001"]');
    await page.locator('#options').evaluate(n=>{n.open=true;});
    await page.locator('#search').fill('needle-first');await page.waitForSelector('[data-id="1"]');
    assert(await page.locator('.entry').count()===1,'Search did not reach oldest entry');
    await page.locator('#view').selectOption('zh');assert(await page.locator('.entry .en').isHidden(),'Chinese-only view');
    await page.locator('#view').selectOption('en');assert(await page.locator('.entry .zh').isHidden(),'English-only view');
    await page.locator('#view').selectOption('both');
    const fontBefore=await page.locator('.text').first().evaluate(n=>parseFloat(getComputedStyle(n).fontSize));
    await page.locator('#larger').click();assert(await page.locator('.text').first().evaluate(n=>parseFloat(getComputedStyle(n).fontSize))===fontBefore+2,'Text size control');
    await page.evaluate(()=>{document.execCommand=command=>{if(command==='copy'){window.copied=document.activeElement.value;return true;}return false;};});
    // Loopback may expose the secure clipboard API; explicitly exercise the HTTP fallback.
    await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{value:undefined,configurable:true}));
    await page.locator('#copy').click();assert(await page.evaluate(()=>window.copied.includes('needle-first')&&(window.copied.includes('中文')||window.copied.includes('项目风险'))),'Copy visible bilingual text');
    await page.locator('.entry button').click();assert(await page.locator('.entry button').textContent()==='Copied','Per-entry copy feedback');
    result.checks.push('Whole-history search, all language views, font size, HTTP clipboard fallback');
    await page.locator('#live').click();await page.waitForSelector('[data-id="10001"]');
    await context.setOffline(true);await page.waitForFunction(()=>document.getElementById('connection').textContent.includes('Reconnecting'));
    assert(await page.locator('[data-id="10001"]').count()===1,'Received text vanished offline');
    fixture('reconnect');await context.setOffline(false);await page.waitForSelector('[data-id="10002"]',{timeout:12000});
    await page.reload();await page.waitForSelector('[data-id="10002"]');
    result.checks.push('Temporary disconnect and refresh recover without duplicate turns');
    await page.locator('#options').evaluate(n=>{n.open=true;});
    const downloaded=page.waitForEvent('download');await page.locator('#download').click();const download=await downloaded;
    assert(!(await download.failure()),'Browser download failed');
    const chunks=[];for await(const chunk of await download.createReadStream())chunks.push(chunk);
    const text=Buffer.concat(chunks).toString('utf8');
    assert(text.includes('needle-first')&&text.includes('New after reconnect')&&text.includes('延迟的完整译文。'.repeat(400)),'Full TXT download incomplete');
    assert((text.match(/ · spoken: /g)||[]).length===10002,'Downloaded entries missing/duplicated');
    result.checks.push('Download contains all 10,002 entries and untruncated delayed text');
    const phones=[];
    for(let i=0;i<8;i++)phones.push(await browser.newContext({...devices[i%2?'Pixel 7':'iPhone 13']}));
    await Promise.all(phones.map(async c=>{const p=await c.newPage();await p.goto(url);await p.waitForSelector('[data-id="10002"]');assert(await p.locator('.entry').count()<=120,'Unbounded phone DOM');await c.close();}));
    assert(!outside.length,'External web request: '+outside.join(','));assert(!jsErrors.length,jsErrors.join(','));
    assert(!(await page.evaluate(()=>window.injected)),'Caption markup executed');
    await page.locator('#options').evaluate(n=>{n.open=false;});
    await page.screenshot({path:path.join(art,'phone-live.png')});
    result.checks.push('Eight simultaneous emulated phones; no remote assets or script injection');
    result.passed=true;
  }finally{
    if(browser)await browser.close();helper.stdin.end();await Promise.race([new Promise(r=>helper.on('exit',r)),wait(3000)]);if(helper.exitCode===null)helper.kill();
    fs.writeFileSync(path.join(art,'result.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
  }
})().catch(e=>{console.error(e);process.exitCode=1;});
