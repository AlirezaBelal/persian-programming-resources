import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const out=process.env.QA_OUTPUT||'../masir-qa-evidence';await mkdir(out,{recursive:true});
const url=process.env.PRODUCT_URL||'http://127.0.0.1:8765/';
const catalog=JSON.parse(await readFile(process.env.CATALOG_PATH||'docs/resources.json','utf8'));
const browser=await chromium.launch();const reports=[];
async function ready(page){await page.locator('.resource').first().waitFor();await page.evaluate(()=>document.fonts.ready);}
async function inspect(page,label,width){
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'page overflow '+label+' '+width);
 assert(await page.locator('img').evaluateAll(xs=>xs.every(x=>x.complete&&x.naturalWidth>0)),'broken image');
 const scan=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();await writeFile(out+'/'+label+'-'+width+'-accessibility.json',JSON.stringify(scan,null,2));
 assert.deepEqual(scan.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),[],'accessibility');
 return scan.violations.length;
}
try{for(const width of [320,375,390,768,1024,1440,1920]){
 const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});const page=await context.newPage();const errors=[],bad=[],requests=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('response',r=>{if(r.status()>=400)bad.push([r.status(),r.url()]);});page.on('request',r=>requests.push(r.url()));
 await page.goto(url,{waitUntil:'networkidle'});await ready(page);
 assert.equal(await page.locator('html').getAttribute('dir'),'rtl');assert.equal(await page.locator('h1').count(),1);assert.match(await page.title(),/مسیر یادگیری/);
 assert(await page.locator('h1').evaluate(e=>parseFloat(getComputedStyle(e).fontSize)<=56));assert(await page.evaluate(()=>document.fonts.check('16px Vazirmatn')),'local font');
 assert.equal(await page.locator('#count').textContent(),new Intl.NumberFormat('fa-IR').format(catalog.resources.length));assert.equal(await page.locator('.resource').count(),12);
 for(const a of await page.locator('a[href^="#"]').all()){const href=await a.getAttribute('href');assert(await page.locator(href).count(),'anchor '+href);}
 const hrefs=await page.locator('.resource-link').evaluateAll(xs=>xs.map(a=>a.href));assert.deepEqual(hrefs,catalog.resources.slice(0,12).map(r=>new URL(r.url).href));
 for(const a of await page.locator('.resource-link,.catalog-link').all()){assert.equal(await a.getAttribute('rel'),'noopener noreferrer');assert.equal(await a.getAttribute('target'),'_blank');}
 await page.screenshot({path:out+'/product-'+width+'.png',fullPage:true});
 await page.keyboard.press('Tab');assert(await page.evaluate(()=>document.activeElement!==document.body&&getComputedStyle(document.activeElement).outlineStyle!=='none'),'visible keyboard focus');
 await page.locator('.hero-actions a[href="#directory"]').click();assert.equal(new URL(page.url()).hash,'#directory');
 await page.locator('#query').fill('Python');assert(await page.locator('.resource').count()>0);assert.match(await page.locator('#active-filters').textContent(),/Python/);
 await page.locator('#category').selectOption('کتاب‌ها');await page.locator('#kind').selectOption('کتاب و متن');await page.locator('#topic').selectOption('پایتون');
 assert.equal(await page.locator('.resource').count(),catalog.resources.filter(r=>r.category==='کتاب‌ها'&&r.topic==='پایتون').length);
 await page.locator('#query').fill('synthetic-no-resource-match');assert(await page.locator('#empty').isVisible());assert.equal(await page.locator('.resource').count(),0);
 await page.locator('#empty-reset').focus();await page.keyboard.press('Space');assert.equal(await page.locator('.resource').count(),12);assert.equal(await page.locator('#query').inputValue(),'');
 await page.locator('#categories button[data-category="کانال‌های یوتیوب"]').focus();await page.keyboard.press('Enter');assert.equal(await page.locator('#category').inputValue(),'کانال‌های یوتیوب');assert.equal(await page.locator('.resource h3').first().textContent(),'جادی');
 await page.locator('#reset').click();await page.locator('#next').click();assert.equal(await page.locator('.resource-link').first().getAttribute('href'),catalog.resources[12].url);assert.equal(await page.locator('#results-heading').evaluate(e=>e===document.activeElement),true);
 await page.locator('#reset').click();const violations=await inspect(page,'product',width);
 // Combined controls and populated results are checked at every requested viewport.
 assert.equal(await page.locator('#summary').getAttribute('role'),'status');assert.equal(await page.locator('#summary').getAttribute('aria-live'),'polite');
 if(width===375||width===1440){await page.locator('#query').fill('گیت');await page.locator('#directory').screenshot({path:out+'/directory-'+width+'.png'});if(width===1440){await page.locator('#directory').scrollIntoViewIfNeeded();await page.screenshot({path:out+'/portfolio-preview.png',fullPage:false});}await page.locator('#reset').click();}
 assert.deepEqual(errors,[]);assert.deepEqual(bad,[]);const external=requests.filter(u=>/^https?:/.test(u)&&new URL(u).origin!==new URL(url).origin);assert.deepEqual(external,[],'unexpected external calls');
 reports.push({width,url,overflow:'passed',search:'passed',categoryTypeTopic:'passed',reset:'passed',pagination:'passed',keyboard:'passed',accessibilityViolations:violations,external,browserErrors:errors,hero:await page.locator('h1').evaluate(e=>getComputedStyle(e).fontSize)});
 await context.close();
}
// Deterministic malformed-catalog, retry, and HTML-injection tests; no publisher requests.
const context=await browser.newContext({viewport:{width:375,height:900}});const page=await context.newPage();let malformed=true;
await page.route('**/resources.json',r=>r.fulfill({contentType:'application/json',body:JSON.stringify(malformed?{resources:[]}:catalog)}));
await page.goto(url);await page.locator('#catalog-error').waitFor({state:'visible'});assert.equal(await page.locator('.resource').count(),0);malformed=false;await page.locator('#retry').click();await ready(page);
await inspect(page,'recovered',375);
const injected=structuredClone(catalog);injected.resources[0].title='<img src="synthetic-x" onerror="alert(1)">';await page.unroute('**/resources.json');await page.route('**/resources.json',r=>r.fulfill({contentType:'application/json',body:JSON.stringify(injected)}));await page.reload();await ready(page);assert.equal(await page.locator('.resource h3').first().textContent(),injected.resources[0].title);assert.equal(await page.locator('.resource img').count(),0);await context.close();
}finally{await writeFile(out+'/results.json',JSON.stringify(reports,null,2));await browser.close();}
