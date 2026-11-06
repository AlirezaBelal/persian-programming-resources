'use strict';
const CATEGORIES=['کتاب‌ها','دوره‌ها','دوره‌های آموزشی در یوتیوب','کانال‌های یوتیوب','منابع تکمیلی'];
const KINDS=['کتاب و متن','دوره','ویدیو','کانال','منبع تکمیلی'];
const SOURCE_PATHS=['کتاب‌ها/README.md','دوره‌ها/README.md','دوره‌های آموزشی در یوتیوب/README.md','کانال‌های یوتیوب/README.md','منابع-تکمیلی/README.md'];
const REPOSITORY='https://github.com/AlirezaBelal/masir-yadgiri';
const TOPIC_ALIASES={'جاوا':'java','پایتون':'python','جاوااسکریپت':'javascript js','گیت':'git','جنگو':'django','ری‌اکت':'react','ریکت':'react','ویو':'vue','گو':'golang','لینوکس':'linux','هوش مصنوعی':'ai machine learning','سی‌اس‌اس':'css','سی پلاس پلاس':'c++','سی شارپ':'c#','تایپ اسکریپت':'typescript','لاراول':'laravel','راست':'rust'};
function normalize(value){return String(value??'').normalize('NFKC').replace(/[يى]/g,'ی').replace(/ك/g,'ک').replace(/[\u064b-\u065f\u0670]/g,'').replace(/\u200c/g,' ').toLocaleLowerCase('fa-IR').replace(/\s+/g,' ').trim();}
function safeUrl(value){try{const u=new URL(value);return ['http:','https:'].includes(u.protocol)&&!u.username&&!u.password&&!/[\s<>"\u0000-\u001f]/u.test(value)&&![...u.searchParams.keys()].some(k=>['token','password','secret','api_key','apikey','access_token','authorization','auth','client_secret','signature'].includes(k.toLowerCase()))&&!['t.me','telegram.me','mega.nz','mediafire.com'].some(h=>u.hostname===h||u.hostname.endsWith('.'+h));}catch{return false;}}
function validateCatalog(data){
 if(!data||data.schemaVersion!==1||!Array.isArray(data.resources)||!data.resources.length||data.resources.length>2000||!Array.isArray(data.sources)||data.sources.length!==5||!/^[a-f0-9]{64}$/.test(data.sourceDigest))throw Error('Invalid catalog');
 const sourceSet=new Set(data.sources.map(s=>s.path));if(sourceSet.size!==5||SOURCE_PATHS.some(p=>!sourceSet.has(p)))throw Error('Invalid sources');
 for(const r of data.resources){if(!r||!['title','url','description','topic','kind','category','source','publisher','access'].every(k=>typeof r[k]==='string')||!r.title.trim()||!r.topic.trim()||!safeUrl(r.url)||!CATEGORIES.includes(r.category)||!KINDS.includes(r.kind)||!SOURCE_PATHS.includes(r.source)||r.category!==CATEGORIES[SOURCE_PATHS.indexOf(r.source)]||r.publisher!==new URL(r.url).hostname||!Number.isInteger(r.sourceLine)||r.sourceLine<1||!Array.isArray(r.flags)||!r.flags.every(f=>typeof f==='string')||!Array.isArray(r.relatedLinks)||!r.relatedLinks.every(l=>typeof l.title==='string'&&safeUrl(l.url)))throw Error('Invalid resource');}
 for(const s of data.sources){if(!/^[a-f0-9]{64}$/.test(s.sha256)||!Number.isInteger(s.count)||s.count<1||s.count!==data.resources.filter(r=>r.source===s.path).length)throw Error('Invalid source count');}
 return data.resources;
}
function filterResources(records,{query='',category='all',kind='all',topic='all'}={}){
 const terms=normalize(query).split(' ').filter(Boolean);
 return records.filter(r=>{if(category!=='all'&&r.category!==category||kind!=='all'&&r.kind!==kind||topic!=='all'&&r.topic!==topic)return false;
 const aliases=Object.entries(TOPIC_ALIASES).filter(([key])=>(' '+normalize(r.topic)+' ').includes(' '+normalize(key)+' ')).map(([,value])=>value).join(' ');
 const haystack=normalize([r.title,r.description,r.topic,r.category,r.kind,r.publisher,...r.flags,aliases].join(' '));return terms.every(term=>haystack.includes(term));});
}
function sourceUrl(record){return REPOSITORY+'/blob/master/'+record.source.split('/').map(encodeURIComponent).join('/')+'#L'+record.sourceLine;}
if(typeof module!=='undefined')module.exports={normalize,safeUrl,validateCatalog,filterResources,sourceUrl,CATEGORIES,KINDS};
if(typeof document!=='undefined'){
 const $=id=>document.getElementById(id),q=$('query'),cat=$('category'),kind=$('kind'),topic=$('topic'),results=$('results');
 const format=new Intl.NumberFormat('fa-IR');const PAGE_SIZE=12;let records=[],page=0,loaded=false,loading=false;
 function el(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
 function link(text,url,cls){const a=el('a',text,cls);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;}
 function card(r){
  const article=el('article',undefined,'resource');
  const meta=el('div',undefined,'card-meta');meta.append(el('span',r.kind,'kind-label'),el('span',r.topic,'topic-label'));
  const title=el('h3',r.title);title.dir='auto';
  const description=el('p',r.description||'توضیح تکمیلی در فهرست ثبت نشده؛ عنوان و شرایط منبع اصلی را بررسی کنید.','description');description.dir='auto';
  const host=el('bdi',r.publisher,'publisher');host.dir='ltr';
  const access=el('p',r.access,'access-note');
  const flags=el('div',undefined,'flags');for(const value of r.flags)flags.append(el('span',value,'flag'));
  const actions=el('div',undefined,'card-actions');actions.append(link('مشاهده منبع',r.url,'resource-link'),link('یادداشت فهرست',sourceUrl(r),'catalog-link'));
  article.append(meta,title,description,host,access,flags);
  if(r.relatedLinks.length){const details=el('details',undefined,'related-links');details.append(el('summary','پیوندهای تکمیلیِ همین مدخل'));for(const related of r.relatedLinks)details.append(link(related.title,related.url));article.append(details);}
  article.append(actions);return article;
 }
 function draw(){
  if(!loaded)return;const found=filterResources(records,{query:q.value,category:cat.value,kind:kind.value,topic:topic.value});
  const pages=Math.max(1,Math.ceil(found.length/PAGE_SIZE));page=Math.max(0,Math.min(page,pages-1));
  results.replaceChildren(...found.slice(page*PAGE_SIZE,(page+1)*PAGE_SIZE).map(card));
  $('empty').hidden=found.length>0;$('pagination').hidden=found.length===0;
  $('summary').textContent=`${format.format(found.length)} مدخل از ${format.format(records.length)} · صفحه ${format.format(page+1)} از ${format.format(pages)}`;
  $('previous').disabled=page===0;$('next').disabled=page+1>=pages;
  const active=[];if(q.value.trim())active.push('جست‌وجو: «'+q.value.trim()+'»');for(const control of [cat,kind,topic])if(control.value!=='all')active.push(control.value);
  $('active-filters').textContent=active.length?active.join(' · '):'همه دسته‌ها و موضوع‌ها؛ بدون فیلتر';
  for(const button of $('categories').querySelectorAll('button'))button.setAttribute('aria-pressed',String(button.dataset.category===cat.value));
 }
 function reset(){q.value='';cat.value='all';kind.value='all';topic.value='all';page=0;draw();}
 function populate(){
  cat.replaceChildren(el('option','همه دسته‌ها'));cat.firstChild.value='all';
  topic.replaceChildren(el('option','همه موضوع‌ها'));topic.firstChild.value='all';
  for(const value of CATEGORIES){const option=el('option',value);option.value=value;cat.append(option);}
  for(const value of [...new Set(records.map(r=>r.topic))].sort((a,b)=>a.localeCompare(b,'fa'))){const option=el('option',value);option.value=value;topic.append(option);}
  $('categories').replaceChildren();
  for(const value of ['all',...CATEGORIES]){const button=el('button');button.type='button';button.dataset.category=value;button.setAttribute('aria-pressed',String(value==='all'));button.append(el('span',value==='all'?'همه منابع':value),el('span',format.format(value==='all'?records.length:records.filter(r=>r.category===value).length),'category-count'));button.addEventListener('click',()=>{cat.value=value;topic.value='all';page=0;draw();});$('categories').append(button);}
 }
 async function load(){
  if(loading)return;loading=true;loaded=false;$('catalog-error').hidden=true;$('catalog-loading').hidden=false;$('catalog-workspace').setAttribute('aria-busy','true');
  try{const response=await fetch('resources.json');if(!response.ok)throw Error('Catalog unavailable');const data=await response.json();records=validateCatalog(data);populate();loaded=true;$('count').textContent=format.format(records.length);$('catalog-version').textContent=data.sourceDigest.slice(0,12);reset();}
  catch{records=[];results.replaceChildren();$('catalog-error').hidden=false;$('summary').textContent='فهرست بارگذاری نشد؛ دوباره تلاش کنید یا مخزن را ببینید.';}
  finally{loading=false;$('catalog-loading').hidden=true;$('catalog-workspace').setAttribute('aria-busy','false');}
 }
 q.addEventListener('input',()=>{page=0;draw();});for(const control of [cat,kind,topic])control.addEventListener('change',()=>{page=0;draw();});
 $('reset').addEventListener('click',reset);$('empty-reset').addEventListener('click',()=>{reset();q.focus();});$('retry').addEventListener('click',load);
 for(const [id,delta]of[['previous',-1],['next',1]])$(id).addEventListener('click',()=>{page+=delta;draw();$('results-heading').focus();});
 load();
}
