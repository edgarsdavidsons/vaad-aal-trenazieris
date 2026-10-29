#!/usr/bin/env python3
"""Merge course and advanced questions into the one canonical VAAD trainer."""
import json, re, base64, html
from pathlib import Path

root=Path(__file__).resolve().parents[1]
page=root/'index.html'
# Always build from the last known good original, not a previously generated page.
# This prevents a broken assets/questions path from being carried into the next build.
import subprocess
historical_blob='9e40c6f2b0de406ef7c0a29dd2acce9366a55b83'
source=subprocess.check_output(['git','cat-file','blob',historical_blob],cwd=root).decode('utf-8')
m=re.search(r'(<script type="application/json" id="app-data">)(.*?)(</script>)',source,re.S)
if not m: raise SystemExit('Missing main app-data JSON')
data=json.loads(m.group(2))
data.setdefault('images',{})
seen={q['q'].strip().casefold() for q in data['questions']}
ids={q['id'] for q in data['questions']}
aliases={'Sakņu sistēmas':'Sakņu sistēmas','Klasifikācija':'Nezāļu klasifikācija','Ierobežošana':'Nezāļu ierobežošana','Nezāļu bioloģija':'Nezāļu bioloģija','Augu augšana':'Augu augšana','Augseka':'Augseka','AAL klasifikācija':'AAL klasifikācija','Rezistence':'Herbicīdu rezistence','Latvāņi':'Latvāņi un karantīna','AAL drošība':'AAL drošība'}
source_id={'Sakņu sistēmas':'NE','Klasifikācija':'NE','Ierobežošana':'NE','Nezāļu bioloģija':'NE','Augu augšana':'LAW','Augseka':'AUG','AAL klasifikācija':'KL','Rezistence':'KL','Latvāņi':'LAT','AAL drošība':'AA'}
extra=(root/'saknu-sistemas.html').read_text(encoding='utf-8')
hit=re.search(r'const QUESTIONS=(\[.*?\]);const KEY=',extra,re.S)
assert hit, 'Supplemental course questions not found'
rows=json.loads(hit.group(1))
new=[]
for i,r in enumerate(rows,1):
    question,correct,w1,w2,w3,why,topic=r
    new.append(dict(id=f'EXT{i:03}',topic=aliases[topic],q=question,opts=[correct,w1,w2,w3],why=why,source=source_id[topic]))

def svg_image(visual):
    # Original simplified teaching diagrams, not photographs of real specimens or actual pesticide labels.
    common='<rect width="460" height="260" rx="15" fill="#f4f7ed"/><rect y="119" width="460" height="141" fill="#e2d8bd"/><path d="M0 119H460" stroke="#9c8c6b" stroke-width="3"/>'
    leaf='<path d="M225 120V48 M225 82Q165 26 150 60Q171 91 225 82 M225 67Q275 20 299 42Q288 72 225 67" stroke="#347b48" stroke-width="6" fill="#9bd79a"/>'
    if visual=='rhizome':
        drawing=leaf+'<path d="M225 120V163 H110 L76 184 M225 163H355L385 183 M165 163V124 M316 163V119" fill="none" stroke="#9c6639" stroke-width="10" stroke-linecap="round"/><path d="M110 163l-14 24m83-24l-11 27m101-27l8 35m70-35l19 25" stroke="#b78d64" stroke-width="4"/>'
    elif visual=='taproot':
        drawing=leaf+'<path d="M225 119 Q210 190 225 248 Q242 185 225 119" fill="#c4976b" stroke="#925b36" stroke-width="5"/><path d="M218 163l-42 25m47 24l-34 20m42-47l35 28m-44 18l-20 20" stroke="#a36c45" stroke-width="4"/>'
    elif visual=='fibrous':
        drawing=leaf+''.join(f'<path d="M225 119 Q{225+(n-6)*8} 178 {110+n*19} 248" fill="none" stroke="#b4885d" stroke-width="4"/>' for n in range(13))
    elif visual=='rootshoot':
        drawing=leaf+'<path d="M225 120V188 Q275 190 345 202 M225 188Q176 192 106 207 M345 202V130 M106 207V131" fill="none" stroke="#9e713f" stroke-width="8"/><path d="M345 130V73m0 25l-29-24m29 14l24-27 M106 131V88m0 20l-20-28m20 12l23-25" stroke="#347b48" stroke-width="6"/>'
    else: drawing=leaf
    if visual.startswith('ghs-'):
        pict={'ghs-exclamation':'!','ghs-environment':'☠︎','ghs-flame':'♨','ghs-skull':'☠','ghs-corrosion':'⚗','ghs-health':'✦'}[visual]
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="460" height="260" viewBox="0 0 460 260"><rect width="460" height="260" fill="#fafafa"/><path d="M230 12L350 130 230 248 110 130Z" fill="white" stroke="#d42e2e" stroke-width="13"/><text x="230" y="172" font-size="106" text-anchor="middle" font-family="sans-serif" fill="#171717">{html.escape(pict)}</text><text x="230" y="254" font-size="11" text-anchor="middle" fill="#666">Mācību simbols — ilustrācija</text></svg>'
    elif visual=='sprayer':
        svg='<svg xmlns="http://www.w3.org/2000/svg" width="460" height="260" viewBox="0 0 460 260"><rect width="460" height="260" fill="#edf5ec"/><path d="M0 215H460" stroke="#7faa63" stroke-width="9"/><rect x="145" y="124" width="128" height="71" rx="12" fill="#70ab62" stroke="#2d6444" stroke-width="5"/><path d="M130 165H45M273 165h144" stroke="#384f48" stroke-width="9"/><circle cx="173" cy="205" r="23" fill="#2d3f38"/><circle cx="267" cy="205" r="23" fill="#2d3f38"/>'+''.join(f'<path d="M{x} 173l-9 30m9-30l9 30" stroke="#5da4dc" stroke-width="3"/>' for x in [50,80,110,310,342,373,406])+'<text x="230" y="54" text-anchor="middle" font-family="sans-serif" font-size="23" fill="#305b41">Smidzināšanas aprēķins</text></svg>'
    else:
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="460" height="260" viewBox="0 0 460 260">{common}{drawing}<text x="12" y="23" font-family="sans-serif" font-size="15" fill="#555">Shematiska ilustrācija (ne mērogā)</text></svg>'
    return 'data:image/svg+xml;base64,'+base64.b64encode(svg.encode('utf-8')).decode('ascii')

advanced=json.loads((root/'data/advanced_questions.json').read_text(encoding='utf-8'))
for i,q in enumerate(advanced,1):
    item=dict(id=f'ADV{i:03}',topic=q['topic'],q=q['q'],opts=q['opts'],why=q['why'],source='PRACT')
    if q.get('visual'):
        key='ADVIMG_'+q['visual']
        data['images'][key]=svg_image(q['visual'])
        item['image']=key
    new.append(item)

added=0
for q in new:
    normalized=q['q'].strip().casefold()
    if normalized in seen: continue
    if q['id'] in ids: raise RuntimeError(f'Duplicate ID {q["id"]}')
    data['questions'].append(q)
    seen.add(normalized); ids.add(q['id']); added+=1

# Ensure every question's source is readable by the main UI.
data['sources'].setdefault('PRACT', {
    'title':'Praktiskie mācību uzdevumi un oriģinālās shēmas',
    'url':'https://www.vaad.gov.lv/lv/macibas-un-apliecibas',
    'type':'Mācību uzdevums'
})
for q in data['questions']:
    if q.get('source') not in data['sources']:
        q['source']='PRACT'

# Weed atlas (photos extracted from materiali/ by build_atlas.py), root systems, teacher test, booklet facts.
# These questions intentionally repeat wording ("Kura nezāle redzama attēlā?"), so they skip text de-duplication.
import sys
sys.path.insert(0,str(root/'scripts'))
import atlas_questions
atlas_new=atlas_questions.build(data,root)
for q in atlas_new:
    if q['id'] in ids: raise RuntimeError(f'Duplicate ID {q["id"]}')
    data['questions'].append(q); ids.add(q['id'])

# Restore the proven original image contract: DATA.images[q.image] is a data URL.
# Never transform those references into file paths. The historical blob contains
# the actual JPEG bytes, unlike the broken generated assets paths.
import subprocess
historical_blob='9e40c6f2b0de406ef7c0a29dd2acce9366a55b83'
original=subprocess.check_output(['git','cat-file','blob',historical_blob],cwd=root).decode('utf-8')
historical_match=re.search(r'<script type="application/json" id="app-data">(.*?)</script>',original,re.S)
if not historical_match:
    raise RuntimeError('Historical original photo dataset not found')
historical=json.loads(historical_match.group(1))
# Restore the original gallery metadata as well as image bytes.
data['weeds']=historical['weeds']
original_images=historical.get('images',{})
if len(original_images)<38:
    raise RuntimeError(f'Expected 38 original weed photos, got {len(original_images)}')
for key,value in original_images.items():
    if not isinstance(value,str) or not value.startswith('data:image/'):
        raise RuntimeError(f'Invalid historical image: {key}')
    data['images'][str(key)]=value

# Restore keys for all questions accidentally rewritten to assets/... paths.
image_urls={v:k for k,v in data['images'].items() if isinstance(v,str)}
for question in data['questions']:
    ref=question.get('image')
    if not isinstance(ref,str):
        continue
    if ref in data['images']:
        continue
    if ref in image_urls:
        question['image']=image_urls[ref]
        continue
    stem=Path(ref.split('?',1)[0]).stem
    if stem in data['images']:
        question['image']=stem
    elif ref.startswith('assets/questions/') and 'ADVIMG_' in ref:
        question['image']=stem

def usable_image(value):
    # Original photos and SVGs are embedded; atlas photos are committed files under assets/atlas/.
    return isinstance(value,str) and (value.startswith('data:image/')
        or (value.startswith('assets/atlas/') and (root/value).is_file()))
bad=[(q['id'],q.get('image')) for q in data['questions']
     if q.get('image') and not usable_image(data['images'].get(str(q['image'])))]
if bad:
    raise RuntimeError(f'Broken image references: {bad[:20]}')
# Every weed gallery image must be a usable inline data URL.
for weed in data['weeds']:
    ref=str(weed['id'])
    value=data['images'].get(ref,'')
    assert value.startswith('data:image/'), f'Gallery image {ref} is not embedded'
assert len(data['weeds'])==38, f'Expected 38 gallery entries, got {len(data["weeds"])}'
print(f'Validated {len(original_images)} original photos and {sum(bool(q.get("image")) for q in data["questions"])} illustrated questions')

payload=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
source=source[:m.start(2)]+payload+source[m.end(2):]
topics=[('Sakņu sistēmas','🌿'),('Nezāļu klasifikācija','🌱'),('Nezāļu ierobežošana','🌾'),('Nezāļu bioloģija','🍃'),('Augu augšana','☀️'),('AAL klasifikācija','🧪'),('Herbicīdu rezistence','🔬'),('AAL drošība','🛡️'),('AAL marķējuma analīze','🏷️'),('Praktiskās situācijas','🧭'),('Vizuālā diagnostika','🔎')]
for name,emoji in topics:
    entry="['"+name+"','"+emoji+"']"
    if entry not in source: source=source.replace('const TOPICS=[','const TOPICS=['+entry+',',1)
# Atlas topics first, in their own order (each insert goes to the front).
for name,emoji in reversed(atlas_questions.TOPICS):
    source=source.replace('const TOPICS=[','const TOPICS=['+"['"+name+"','"+emoji+"'],",1)

def patch(old,new):
    global source
    assert source.count(old)==1, f'Patch anchor not found exactly once: {old[:60]}'
    source=source.replace(old,new,1)

# Weed atlas view: every plant per root system / biological group and the root of every plant.
atlas_topics=json.dumps([list(t) for t in atlas_questions.TOPICS],ensure_ascii=False)
patch("ROOTS=DATA.rootTypes;","ROOTS=DATA.rootTypes, ATLAS=DATA.atlas, ATLAS_TOPICS="+atlas_topics+";")
patch("['roots','♧','Sakņu sistēmas'],","['roots','♧','Sakņu sistēmas'],['atlas','✿','Nezāļu atlants'],")
patch("roots:renderRoots,","roots:renderRoots,atlas:renderAtlas,")
patch("function renderHome(){",r"""let atlasFilter='',atlasMode='root';
function renderAtlas(){return `${topTitle('Nezāļu atlants',`${ATLAS.species.length} nezāles no kursa materiāliem: katrai sakņu sistēmai visi augi un katram augam tā sakņu sistēma un bioloģiskā grupa.`,btn('topic','Trenēties →','btn-primary','data-topic="Sakņu sistēmas ↔ augi"'))}
<div class="toolbar"><input id="atlasSearch" type="search" class="search" placeholder="Meklēt augu, piem., usne..." value="${esc(atlasFilter)}"/><div class="atlas-tabs">${[['root','Pēc sakņu sistēmas'],['group','Pēc bioloģiskās grupas']].map(([m,t])=>btn('atlasMode',t,atlasMode===m?'btn-primary':'btn-light',`data-mode="${m}"`)).join('')}</div></div>
<div id="atlasList">${atlasRows()}</div>
<div class="section-head"><div><h3>Sakņu sistēmu zīmējumi (D. Lapiņš, 2021)</h3><p>Tie paši zīmējumi, kas skolotājas testā. Vispirms mēģini atpazīt, tad atver atbildi.</p></div></div>
<div class="atlas-figs">${ATLAS.rootFigures.map(f=>`<div class="panel atlas-fig"><img src="${DATA.images[f.image]}" loading="lazy" alt="Nezāļu sakņu sistēmu zīmējums"/><details><summary>Rādīt atbildi</summary>${Object.entries(f.labels).map(([k,v])=>`<div>${k?`<b>${k}</b> – `:''}${esc(v)}</div>`).join('')}</details></div>`).join('')}</div>
<div class="section-head"><div><h3>Trenēties ar atlantu</h3><p>Jautājumi veidoti tāpat kā skolotājas „Nezāļu testā”.</p></div></div>
<div class="badge-wrap">${ATLAS_TOPICS.map(([t,i])=>btn('topic',`${i} ${esc(t)} (${Q.filter(q=>q.topic===t).length})`,'btn-outline',`data-topic="${esc(t)}"`)).join('')}${btn('teacherExam','⏱ Tests skolotājas formātā (21)','btn-primary')}</div>`}
function atlasRows(){let term=atlasFilter.toLocaleLowerCase('lv-LV'),match=s=>!term||(s.name+' '+s.latin).toLocaleLowerCase('lv-LV').includes(term);
let sections=atlasMode==='root'?Object.entries(ATLAS.roots).map(([id,r])=>({title:r.name,desc:r.desc,items:ATLAS.species.filter(s=>s.root===id)})):Object.entries(ATLAS.groups).map(([id,g])=>({title:g.life==='Barošanās veids'?g.name:`${g.life} · ${g.name}`,desc:g.desc,items:ATLAS.species.filter(s=>s.group===id)}));
let html=sections.map(sec=>({...sec,items:sec.items.filter(match)})).filter(sec=>sec.items.length).map(sec=>`<section class="panel atlas-sec"><div class="atlas-head"><h3>${esc(sec.title)}</h3><span class="root-tag">${sec.items.length} ${sec.items.length===1?'augs':'augi'}</span></div><p class="small-muted">${esc(sec.desc)}</p><div class="atlas-names">${sec.items.map(s=>esc(s.name)).join(' · ')}</div><div class="atlas-grid">${sec.items.map(atlasCard).join('')}</div></section>`).join('');
return html||'<div class="empty-state"><span class="emoji">🔍</span><h3>Augs nav atrasts</h3><p>Izmēģini citu nosaukumu.</p></div>'}
function atlasCard(s){let g=ATLAS.groups[s.group],r=ATLAS.roots[s.root];
return `<div class="atlas-card"><div class="atlas-pics">${s.images.map(k=>`<img src="${DATA.images[k]}" loading="lazy" alt="${esc(s.name)}"/>`).join('')}</div><b>${esc(s.name)}</b><i>${esc(s.latin)}</i><small>${esc(g.life==='Barošanās veids'?g.name:`${g.life} · ${g.name}`)} · ${esc(s.cls)}</small>${r?`<small class="atlas-root">🌱 ${esc(r.name)}</small>`:''}${s.rootNote?`<small>${esc(s.rootNote)}</small>`:''}</div>`}
function pickTeacher(){let used=new Set(),take=(f,n)=>shuffled(Q.filter(q=>f(q)&&!used.has(q.id))).slice(0,n).map(q=>(used.add(q.id),q.id));
return shuffled([...take(q=>q.topic==='Nezāļu foto atlants',7),...take(q=>q.id.startsWith('ATD-')||(q.id.startsWith('ATR-')&&!!q.image),4),...take(q=>q.topic==='Sakņu sistēmas ↔ augi'&&!q.image,2),...take(q=>q.id.startsWith('ATC-'),2),...take(q=>q.topic==='Nezāļu bukleti'||q.topic==='Herbicīdu rezistence',6)])}
function renderHome(){""")
patch("<div class=\"root-callout\"><span>🌿</span>","""<div class="root-callout"><span>🧑‍🏫</span><div><strong>Jauns: nezāļu atlants un tests skolotājas formātā</strong><p>${ATLAS.species.length} nezāles ar foto, visi augi katrai sakņu sistēmai un 21 jautājuma nezāļu tests tādā formātā kā skolotājas „Nezāļu tests”.</p></div><button data-action="atlas" class="btn btn-primary">Atlants →</button><button data-action="teacherExam" class="btn btn-outline">Tests →</button></div>
<div class="root-callout"><span>🌿</span>""")
patch("${btn('startExam','Sākt eksāmenu →','btn-primary btn-xl')}","${btn('startExam','Sākt eksāmenu →','btn-primary btn-xl')} ${btn('teacherExam','Tests skolotājas formātā (21 jaut., 25 min) →','btn-outline btn-xl')}")
patch("else if(a==='rootsQuiz')","""else if(a==='atlasMode'){atlasMode=e.dataset.mode;render()}
else if(a==='teacherExam'){start(pickTeacher(),'exam',25,'Skolotājas formāta tests')}
else if(a==='rootsQuiz')""")
patch("document.addEventListener('input',e=>{","document.addEventListener('input',e=>{if(e.target.id==='atlasSearch'){atlasFilter=e.target.value;document.getElementById('atlasList').innerHTML=atlasRows()}")
patch("</head>","""<style>
.atlas-tabs{display:flex;gap:8px;flex-wrap:wrap}
.atlas-sec{padding:20px 22px;margin-bottom:16px}
.atlas-head{display:flex;justify-content:space-between;align-items:center;gap:10px}
.atlas-head h3{margin:0;font-size:17px}
.atlas-names{font-size:12px;font-weight:700;color:var(--green);margin:8px 0 14px;line-height:1.6}
.atlas-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(175px,1fr));gap:12px}
.atlas-card{border:1px solid var(--border);border-radius:13px;padding:8px;display:flex;flex-direction:column;gap:3px;font-size:13px;background:var(--card)}
.atlas-pics{display:flex;gap:4px;margin-bottom:5px}
.atlas-pics img{flex:1;min-width:0;height:115px;object-fit:cover;border-radius:9px;background:var(--sage)}
.atlas-card i,.atlas-card small{font-size:11px;color:var(--muted);line-height:1.4}
.atlas-card small.atlas-root{color:var(--green);font-weight:800}
.atlas-figs{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}
.atlas-fig{padding:12px}.atlas-fig img{width:100%;border-radius:9px;background:#fff}
.atlas-fig summary{cursor:pointer;font-weight:800;margin:9px 0 5px;color:var(--green)}
.atlas-fig details div{font-size:13px;padding:2px 0}
.root-callout .btn{flex-shrink:0}
@media(max-width:480px){.atlas-grid{grid-template-columns:1fr 1fr}.atlas-pics img{height:90px}.root-callout{flex-wrap:wrap}}
</style>
</head>""")

# Topic-specific resumability. Preserve exam sessions independently.
source=source.replace('let saved=load();let stats=', 'let saved=load();let topicSessions=saved.topicSessions||{};let stats=',1)
source=source.replace('function save(){try{localStorage.setItem(KEY,JSON.stringify({stats,mistakes,bookmarks,history,session,lastResult}))}',
'''function save(){if(session&&session.mode==='study'&&session.label)topicSessions[session.label]=session;try{localStorage.setItem(KEY,JSON.stringify({stats,mistakes,bookmarks,history,session,lastResult,topicSessions}))}''',1)
old="else if(a==='topic'){start(shuffled(Q.filter(q=>q.topic===e.dataset.topic)).map(q=>q.id),'study',0,e.dataset.topic)}"
replacement="else if(a==='topic'){let t=e.dataset.topic;if(session&&session.mode==='study'&&session.label===t){go('session')}else if(topicSessions[t]&&topicSessions[t].ids.every(id=>BYID[id])){if(session&&session.mode==='study'&&session.label)topicSessions[session.label]=session;session=topicSessions[t];save();go('session')}else{start(shuffled(Q.filter(q=>q.topic===t)).map(q=>q.id),'study',0,t)}}"
source=source.replace(old,replacement,1)

# Replace stale hard-coded bank totals with current data counts.
source=source.replace('<strong>221</strong>','<strong>${Q.length}</strong>').replace(' / 221</span>',' / ${Q.length}</span>')
source=source.replace('221 izstrādāts jautājums','Daudzveidīgi mācību jautājumi')
source=source.replace('11 tematiskas sadaļas','${TOPICS.length} tematiskas sadaļas')
source=source.replace('213 teksta + 38 foto + 6 sakņu shēmas','Dažādi jautājumi, foto un shēmas')
# Resolve both source lookups using source objects that always have valid fields.
# Existing app stores SOURCES in an array and question source references can be stale.
source=source.replace("SOURCES[q.source].url", "(SOURCES[q.source]||{url:'#',type:'Mācību materiāls'}).url")
source=source.replace("SOURCES[q.source].type", "(SOURCES[q.source]||{url:'#',type:'Mācību materiāls'}).type")
source=source.replace("SOURCES[q.source].title", "(SOURCES[q.source]||{url:'#',type:'Mācību materiāls'}).title")
# Also provide fallback for a local variable named src in renderers.
source=source.replace("let src=SOURCES[q.source];", "let src=SOURCES[q.source]||{url:'#',type:'Mācību materiāls',title:'Mācību materiāls'};")
# Defensive rendering: unknown source codes must not crash the entire question view.
source=source.replace("let src=SOURCES[q.source];", "let src=SOURCES[q.source]||SOURCES['AA']||{url:'#',type:'Mācības',title:'Mācību materiāls'};")
# A saved interrupted session may point to obsolete IDs after a bank migration.
source=source.replace("function sessionQuestion(){if(!session)return renderHome();", "function sessionQuestion(){if(!session)return renderHome();if(!BYID[session.ids[session.idx]]){session=null;save();return renderHome();}")
page.write_text(source,encoding='utf-8')
assert len(data['questions'])>=350, len(data['questions'])
assert len(ids)==len(data['questions'])
print(f'UNIFIED: {len(data["questions"])} total, {added} added, {len(advanced)} advanced; images={len(data["images"])}')
