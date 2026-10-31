// "Jautā asistentam": Claude answers questions about the trainer's content using tools that
// search the page's own data (questions, weed atlas, MK noteikumi Nr. 950). Same tools as
// scripts/mcp_server.py. On our own server nginx proxies api/claude/messages and adds the API key
// there (deploy/nginx-claude.conf), so visitors need no key. Elsewhere (GitHub Pages) each user enters
// their own key, kept only in this browser's localStorage – never in the repository or the page.
// Loaded before the main script; uses its globals (DATA, Q, esc, btn, topTitle, render) at call time.

const ASK_KEY_STORE='vaad-aal-anthropic-key',ASK_MODEL='claude-opus-5-5';
const ASK_SYSTEM='Tu esi VAAD augu aizsardzības līdzekļu (AAL) 2. reģistrācijas klases lietotāju mācību asistents šajā trenažierī. '+
'Atbildi latviski, ja vien lietotājs nejautā citā valodā, īsi un skaidri. Faktus ņem no rīku rezultātiem (trenažiera jautājumi, '+
'nezāļu atlants, MK noteikumi Nr. 950): pirms atbildes meklē un norādi avotu, piem. „MK Nr. 950, 18.1. punkts”. '+
'Ja rīki neko neatrod, saki to, nevis min. Trenažieris nav oficiāls VAAD eksāmens.';
let askMessages=[],askLog=[],askBusy=false,askStatus='',askDraft='',askProxy=null;
function askProbe(){askProxy='checking';fetch('api/claude/status').then(r=>r.ok?r.text():'').then(t=>t.trim()==='ok',()=>false).then(ok=>{askProxy=ok;if(view==='ask')render()})}

function askGetKey(){try{return localStorage.getItem(ASK_KEY_STORE)||''}catch(e){return ''}}
function askSetKey(k){try{k?localStorage.setItem(ASK_KEY_STORE,k):localStorage.removeItem(ASK_KEY_STORE)}catch(e){}}

// --- Search over the page data (mirrors scripts/knowledge.py) ---
const askFold=t=>String(t??'').toLocaleLowerCase('lv-LV').normalize('NFKD').replace(/\p{M}/gu,'');
const askStems=t=>(askFold(t).match(/[a-z0-9]+/g)||[]).filter(w=>w.length>=3||/^\d+$/.test(w)).map(w=>w.slice(0,5));
const askCount=list=>list.reduce((m,w)=>(m[w]=(m[w]||0)+1,m),{});
let askDocs=null;
function askQuestion(q){let s=DATA.sources[q.source]||{};return {id:q.id,topic:q.topic,question:q.q,correct_answer:q.opts[0],wrong_options:q.opts.slice(1),explanation:q.why||'',has_image:!!q.image,source:s.title||q.source||''}}
function askIndex(){if(askDocs)return askDocs;let d=[],A=DATA.atlas||{},G=A.groups||{},R=A.roots||{},sp=A.species||[];
let add=(kind,id,title,text,content)=>d.push({kind,id,title,content,body:askCount(askStems(text)),head:askCount(askStems(title))});
for(let q of DATA.questions)add('question',q.id,q.q,`${q.q} ${q.opts[0]} ${q.why||''} ${q.topic}`,q);
for(let s of sp){let g=G[s.group]||{},r=R[s.root]||{},info={name:s.name,latin:s.latin,class:s.cls,biological_group:g.name,group_description:g.desc,life:g.life,root_system:r.name,root_description:r.desc};add('weed',s.id,s.name,Object.values(info).filter(Boolean).join(' '),info)}
for(let [k,g] of Object.entries(G))add('biological_group',k,g.name,`${g.name} bioloģiskā grupa ${g.desc||''}`,{group:g.name,life:g.life,description:g.desc,weeds:sp.filter(s=>s.group===k).map(s=>s.name)});
for(let [k,r] of Object.entries(R))add('root_system',k,r.name,`${r.name} sakņu sistēma ${r.desc||''}`,{root_system:r.name,description:r.desc,weeds:sp.filter(s=>s.root===k).map(s=>s.name)});
for(let r of DATA.rootTypes||[])add('root_type',r.id,r.name,Object.values(r).join(' '),r);
for(let [n,t] of Object.entries(DATA.mk950?.points||{}))add('mk950_point',n,`MK Nr. 950, ${n}. punkts`,t,{point:n,text:t,url:DATA.mk950.url});
return askDocs=d}
function askSearch(query,kinds,limit=10){let terms=[...new Set(askStems(query))];if(!terms.length)return [];
let hits=[];for(let x of askIndex()){if(kinds?.length&&!kinds.includes(x.kind))continue;let m=terms.filter(t=>x.body[t]);if(!m.length)continue;
hits.push([m.length/terms.length*10+m.filter(t=>x.head[t]).length+Math.min(m.reduce((s,t)=>s+x.body[t],0),5)*.1,x])}
return hits.sort((a,b)=>b[0]-a[0]).slice(0,limit).map(([s,x])=>({kind:x.kind,id:x.id,title:x.title,score:Math.round(s*100)/100,content:x.kind==='question'?askQuestion(x.content):x.content}))}

const ASK_KINDS=['question','weed','biological_group','root_system','root_type','mk950_point'];
const ASK_TOOLS=[
{name:'search',description:'Meklē visā trenažiera saturā (jautājumi ar atbildēm un skaidrojumiem, nezāļu atlants, bioloģiskās grupas, sakņu sistēmas, MK noteikumu Nr. 950 punkti). Vaicājumu raksti latviski ar atslēgvārdiem; garumzīmes nav obligātas.',
 input_schema:{type:'object',properties:{query:{type:'string'},kinds:{type:'array',items:{type:'string',enum:ASK_KINDS}},limit:{type:'integer',minimum:1,maximum:30}},required:['query'],additionalProperties:false}},
{name:'mk950_point',description:'MK 13.12.2011. noteikumu Nr. 950 punkta pilns teksts ar apakšpunktiem (piem. "18" vai "18.1"; iestarpinātie punkti "13¹", "21¹", "41¹").',
 input_schema:{type:'object',properties:{point:{type:'string'}},required:['point'],additionalProperties:false}},
{name:'list_topics',description:'Trenažiera tēmas un jautājumu skaits katrā.',input_schema:{type:'object',properties:{},additionalProperties:false}},
{name:'topic_questions',description:'Tēmas jautājumi ar pareizajām atbildēm un skaidrojumiem (lapošana ar offset).',
 input_schema:{type:'object',properties:{topic:{type:'string'},limit:{type:'integer',minimum:1,maximum:100},offset:{type:'integer',minimum:0}},required:['topic'],additionalProperties:false}}];
function askRunTool(name,a){
if(name==='search')return askSearch(a.query,a.kinds,a.limit||10);
if(name==='mk950_point'){let p=String(a.point).trim().replace(/\.$/,'').replace('^1','¹'),pts=Object.entries(DATA.mk950?.points||{}).filter(([k])=>k===p||k.startsWith(p+'.'));return pts.length?{url:DATA.mk950.url,points:Object.fromEntries(pts)}:{error:`Punkts ${p} nav atrasts`}}
if(name==='list_topics'){let c={};for(let q of DATA.questions)c[q.topic]=(c[q.topic]||0)+1;return Object.entries(c).map(([topic,questions])=>({topic,questions}))}
if(name==='topic_questions'){let qs=DATA.questions.filter(q=>askFold(q.topic)===askFold(a.topic)),o=a.offset||0;return {topic:a.topic,total:qs.length,questions:qs.slice(o,o+(a.limit||30)).map(askQuestion)}}
throw new Error('Nezināms rīks '+name)}

// --- Claude API (direct browser access with the user's own key) ---
async function askCall(key){let h={'content-type':'application/json','anthropic-version':'2026-10-21','anthropic-beta':'server-side-fallback-2026-07-01'};
if(!askProxy){h['x-api-key']=key;h['anthropic-dangerous-direct-browser-access']='true'}
let r=await fetch(askProxy?'api/claude/messages':'https://api.anthropic.com/v1/messages',{method:'POST',headers:h,
body:JSON.stringify({model:ASK_MODEL,max_tokens:16000,system:ASK_SYSTEM,tools:ASK_TOOLS,messages:askMessages,thinking:{type:'adaptive'},output_config:{effort:'medium'},fallbacks:'default'})});
let j=await r.json().catch(()=>({}));
if(!r.ok){let m=j.error?.message||r.statusText;throw new Error(r.status===401?'API atslēga nav derīga. Ievadi to vēlreiz.':r.status===429?'Pārsniegts pieprasījumu limits, pamēģini pēc brīža.':`API kļūda ${r.status}: ${m}`)}
return j}
async function askSend(text){let key=askProxy===true?'':askGetKey();if((askProxy!==true&&!key)||askBusy||!text.trim())return;
let start=askMessages.length;askBusy=true;askDraft='';askLog.push({role:'user',text});askMessages.push({role:'user',content:text});askStatus='Domā…';askDraw();
try{for(let turn=0;turn<12;turn++){let res=await askCall(key);askMessages.push({role:'assistant',content:res.content});
if(res.stop_reason==='refusal'){askLog.push({role:'assistant',text:'(Modelis atteicās atbildēt uz šo jautājumu.)'});break}
if(res.stop_reason==='pause_turn')continue;
let uses=res.content.filter(b=>b.type==='tool_use');
if(!uses.length){askLog.push({role:'assistant',text:res.content.filter(b=>b.type==='text').map(b=>b.text).join('')});break}
askStatus=uses.map(u=>u.name==='search'?`Meklē: ${u.input.query}`:u.name==='mk950_point'?`Atver MK 950 ${u.input.point}. punktu`:'Skatās tēmas').join(' · ');askDraw();
askMessages.push({role:'user',content:uses.map(u=>{try{return {type:'tool_result',tool_use_id:u.id,content:JSON.stringify(askRunTool(u.name,u.input))}}catch(e){return {type:'tool_result',tool_use_id:u.id,content:String(e.message),is_error:true}}})})}}
catch(e){askMessages.length=start;askLog.push({role:'error',text:e.message||String(e)})}
askBusy=false;askStatus='';askDraw()}

// --- View ---
function askMd(t){let lines=esc(t).replace(/\*\*(.+?)\*\*/g,'<b>$1</b>').replace(/\*(\S[^*\n]*?)\*/g,'<i>$1</i>').replace(/`([^`]+)`/g,'<code>$1</code>').split('\n'),out='',list=false;
for(let l of lines){let m=l.match(/^\s*(?:[-*•]|\d+\.)\s+(.*)/);if(m){if(!list){out+='<ul>';list=true}out+=`<li>${m[1]}</li>`;continue}if(list){out+='</ul>';list=false}
let h=l.match(/^#{1,4}\s+(.*)/);out+=h?`<h4>${h[1]}</h4>`:l.trim()?`<p>${l}</p>`:''}
return out+(list?'</ul>':'')}
function askBubbles(){return askLog.map(m=>`<div class="ask-msg ${m.role}">${m.role==='user'?esc(m.text):askMd(m.text)}</div>`).join('')+(askBusy?`<div class="ask-msg assistant pending">${esc(askStatus||'Domā…')}</div>`:'')}
function askDraw(){let el=document.getElementById('askLog');if(!el){if(typeof view!=='undefined'&&view==='ask')render();return}
el.innerHTML=askBubbles()||askEmpty();el.scrollTop=el.scrollHeight;let b=document.getElementById('askSendBtn');if(b)b.disabled=askBusy}
const ASK_EXAMPLES=['Pie kāda vēja ātruma drīkst smidzināt?','Kādas nezāles ir ar sakneņiem?','Ko MK 950 saka par kodinātām sēklām?','Kā atšķiras ziemotspējīgās un ziemājās nezāles?'];
function askEmpty(){return `<div class="ask-empty"><p>Jautā par jebko no trenažiera: noteikumiem, nezālēm, sakņu sistēmām, AAL lietošanu. Piemēri:</p>${ASK_EXAMPLES.map(x=>btn('askExample',esc(x),'btn-light',`data-q="${esc(x)}"`)).join('')}</div>`}
function renderAsk(){if(askProxy===null)askProbe();
if(askProxy==='checking')return `${topTitle('Jautā asistentam')}<div class="panel ask-setup">Ielādē…</div>`;
let key=askGetKey();
if(askProxy===false&&!key)return `${topTitle('Jautā asistentam','Claude atbild uz jautājumiem par visu trenažiera saturu un norāda avotu.')}
<div class="panel ask-setup"><h3>Ievadi savu Claude API atslēgu</h3><p class="small-muted">Atslēga tiek saglabāta tikai šajā pārlūkā (localStorage) un sūtīta tikai uz api.anthropic.com. Tā nav redzama citiem lapas apmeklētājiem. Neizmanto šo kopīgā datorā.</p>
<input id="askKeyInput" type="password" class="search" autocomplete="off" placeholder="sk-ant-..."/> ${btn('askSaveKey','Saglabāt')}</div>`;
return `${topTitle('Jautā asistentam','Claude atbild uz jautājumiem par visu trenažiera saturu (jautājumi, atlants, MK noteikumi Nr. 950) un norāda avotu.',`<div class="ask-tools">${btn('askClear','Jauna saruna','btn-light')}${askProxy?'':' '+btn('askForget','Aizmirst atslēgu','btn-light')}</div>`)}
<div class="panel ask-panel"><div id="askLog" class="ask-log">${askBubbles()||askEmpty()}</div>
<div class="ask-input"><textarea id="askText" rows="2" placeholder="Raksti jautājumu… (Enter – sūtīt, Shift+Enter – jauna rinda)">${esc(askDraft)}</textarea>${btn('askSendNow','Sūtīt','btn-primary',`id="askSendBtn" ${askBusy?'disabled':''}`)}</div></div>`}
function askAction(a,e){
if(a==='askSaveKey'){let k=document.getElementById('askKeyInput').value.trim();if(k){askSetKey(k);render()}return true}
if(a==='askForget'){askSetKey('');askMessages=[];askLog=[];render();return true}
if(a==='askClear'){if(!askBusy){askMessages=[];askLog=[];render()}return true}
if(a==='askExample'){askSend(e.dataset.q);return true}
if(a==='askSendNow'){if(askBusy)return true;let t=document.getElementById('askText');let v=t.value;t.value='';askSend(v);return true}
return false}
document.addEventListener('keydown',e=>{if(e.target.id==='askText'&&e.key==='Enter'&&!e.shiftKey){e.preventDefault();if(askBusy)return;let v=e.target.value;e.target.value='';askSend(v)}
if(e.target.id==='askKeyInput'&&e.key==='Enter'){askAction('askSaveKey')}});
document.addEventListener('input',e=>{if(e.target.id==='askText')askDraft=e.target.value});
