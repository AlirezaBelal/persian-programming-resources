const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const d=require('../docs/app.js');
const html=fs.readFileSync('docs/index.html','utf8');
const catalog=JSON.parse(fs.readFileSync('docs/resources.json','utf8'));
test('directory is Persian RTL with local catalog source and source attribution',()=>{
 assert.match(html,/<html lang="fa" dir="rtl">/);assert.match(html,/github.com\/AlirezaBelal\/masir-yadgiri/);
 assert.match(fs.readFileSync('docs/app.js','utf8'),/fetch\('resources.json'\)/);assert.match(html,/font-src 'self'/);
});
test('catalog generation is limited to the five tracked catalogs',()=>{
 assert.equal(catalog.sources.length,5);assert.equal(d.validateCatalog(catalog).length,catalog.resources.length);
 assert.equal(new Set(catalog.resources.map(r=>r.category)).size,5);
});
test('search, category, type and reset interactions exist',()=>{
 for(const id of ['query','category','kind','topic','reset','empty-reset'])assert.ok(html.includes(`id="${id}"`));
 assert.deepEqual(d.filterResources(catalog.resources,{}),catalog.resources);
 const row=catalog.resources.find(r=>r.topic==='پایتون'&&r.category==='کتاب‌ها');
 assert.ok(d.filterResources(catalog.resources,{query:'python',category:row.category,kind:row.kind,topic:row.topic}).includes(row));
 assert.equal(d.filterResources(catalog.resources,{query:'impossible-synthetic-term'}).length,0);
});
test('external resources render as escaped text with safe link targets',()=>{
 const app=fs.readFileSync('docs/app.js','utf8');assert.match(app,/e\.textContent=text/);assert.doesNotMatch(app,/innerHTML|insertAdjacentHTML/);
 assert.match(app,/noopener noreferrer/);assert.match(d.sourceUrl(catalog.resources[0]),/masir-yadgiri\/blob\/master\/.+#L\d+$/);
});
test('search normalizes Persian/Arabic letter forms, half-spaces and topic aliases',()=>{
 assert.equal(d.normalize('كِتاب يک'),d.normalize('کتاب یک'));
 assert.equal(d.normalize('تست‌نویسی'),d.normalize('تست نویسی'));
 assert.ok(d.filterResources(catalog.resources,{query:'کانال python'}).length>0);
 assert.ok(d.filterResources(catalog.resources,{query:'طراحی نرم‌افزار'}).length>0);
});
test('filter combinations use intersection and preserve source order',()=>{
 for(const category of d.CATEGORIES)for(const kind of d.KINDS){
  assert.deepEqual(d.filterResources(catalog.resources,{category,kind}),catalog.resources.filter(r=>r.category===category&&r.kind===kind));
 }
});
test('unsafe links and malformed catalogs fail closed',()=>{
 for(const url of ['javascript:alert(1)','data:text/html,test','https://user:pass@example.org','https://example.org/?token=synthetic','https://t.me/test','//example.org'])assert.equal(d.safeUrl(url),false);
 for(const patch of [{resources:[]},{schemaVersion:99},{sourceDigest:'bad'},{sources:[]}])assert.throws(()=>d.validateCatalog({...catalog,...patch}));
 for(const patch of [{url:'javascript:alert(1)'},{source:'outside/README.md'},{title:''},{sourceLine:0},{flags:null},{relatedLinks:[{title:'bad',url:'javascript:test'}]}]){
  assert.throws(()=>d.validateCatalog({...catalog,resources:[{...catalog.resources[0],...patch}]}));
 }
});
test('channel identity, access notes and related source links remain meaningful',()=>{
 const channel=catalog.resources.find(r=>r.url==='https://www.youtube.com/@JadiMirmirani');
 assert.equal(channel.title,'جادی');assert.match(channel.description,/Python/);
 assert.ok(catalog.resources.some(r=>r.flags.includes('مجوز ترجمه نیازمند بررسی')));
 assert.ok(catalog.resources.some(r=>r.flags.includes('نشانی نیازمند بررسی')));
 assert.ok(catalog.resources.some(r=>r.relatedLinks.some(l=>l.url==='https://docs.docker.com/ai/sandboxes/cloud/')));
});
