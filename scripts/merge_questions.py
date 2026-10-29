#!/usr/bin/env python3
"""Merge course and advanced questions into the one canonical VAAD trainer."""
import json, re, base64, html
from pathlib import Path

root=Path(__file__).resolve().parents[1]
page=root/'index.html'
source=page.read_text(encoding='utf-8')
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
        if key not in data['images']: data['images'][key]=svg_image(q['visual'])
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

bad=[(q['id'],q.get('image')) for q in data['questions']
     if q.get('image') and not (
        isinstance(data['images'].get(str(q['image'])),str)
        and data['images'][str(q['image'])].startswith('data:image/'))]
if bad:
    raise RuntimeError(f'Broken image references: {bad[:20]}')
print(f'Validated {len(original_images)} original photos and {sum(bool(q.get("image")) for q in data["questions"])} illustrated questions')

payload=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
source=source[:m.start(2)]+payload+source[m.end(2):]
topics=[('Sakņu sistēmas','🌿'),('Nezāļu klasifikācija','🌱'),('Nezāļu ierobežošana','🌾'),('Nezāļu bioloģija','🍃'),('Augu augšana','☀️'),('AAL klasifikācija','🧪'),('Herbicīdu rezistence','🔬'),('AAL drošība','🛡️'),('AAL marķējuma analīze','🏷️'),('Praktiskās situācijas','🧭'),('Vizuālā diagnostika','🔎')]
for name,emoji in topics:
    entry="['"+name+"','"+emoji+"']"
    if entry not in source: source=source.replace('const TOPICS=[','const TOPICS=['+entry+',',1)

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
