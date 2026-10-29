#!/usr/bin/env python3
"""Merge supplemental VAAD questions into the main index.html during Pages deployment."""
import json, re, html as html_lib
from pathlib import Path

root=Path(__file__).resolve().parents[1]
index=root/'index.html'
addon=root/'saknu-sistemas.html'
source=index.read_text(encoding='utf-8')
extra=addon.read_text(encoding='utf-8')
m=re.search(r'const QUESTIONS=(\[.*?\]);const KEY=',extra,re.S)
assert m, 'Supplemental questions missing'
rows=json.loads(m.group(1))
m=re.search(r'(<script type="application/json" id="app-data">)(.*?)(</script>)',source,re.S)
assert m, 'Main question data missing'
data=json.loads(m.group(2))
existing={q['q'].strip().casefold() for q in data['questions']}
aliases={'Sakņu sistēmas':'Sakņu sistēmas','Klasifikācija':'Nezāļu klasifikācija','Ierobežošana':'Nezāļu ierobežošana','Nezāļu bioloģija':'Nezāļu bioloģija','Augu augšana':'Augu augšana','Augseka':'Augseka','AAL klasifikācija':'AAL klasifikācija','Rezistence':'Herbicīdu rezistence','Latvāņi':'Latvāņi un karantīna','AAL drošība':'AAL drošība'}
source_id={'Sakņu sistēmas':'NE','Klasifikācija':'NE','Ierobežošana':'NE','Nezāļu bioloģija':'NE','Augu augšana':'LAW','Augseka':'AUG','AAL klasifikācija':'KL','Rezistence':'KL','Latvāņi':'LAT','AAL drošība':'AA'}
added=0
for i,r in enumerate(rows,1):
    question,correct,wrong1,wrong2,wrong3,why,topic=r
    if question.strip().casefold() in existing: continue
    data['questions'].append({'id':f'EXT{i:03}', 'topic':aliases[topic], 'q':question,
     'opts':[correct,wrong1,wrong2,wrong3], 'why':why, 'source':source_id[topic]})
    added+=1
    existing.add(question.strip().casefold())
payload=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
source=source[:m.start(2)]+payload+source[m.end(2):]
for label,emoji in [('Sakņu sistēmas','🌿'),('Nezāļu klasifikācija','🌱'),('Nezāļu ierobežošana','🌾'),('Nezāļu bioloģija','🍃'),('Augu augšana','☀️'),('AAL klasifikācija','🧪'),('Herbicīdu rezistence','🔬'),('AAL drošība','🛡️')]:
    entry="['"+label+"','"+emoji+"']"
    if entry not in source:
        source=source.replace("const TOPICS=[", "const TOPICS=["+entry+",",1)
# The original interface already pulls topic questions from Q and uses Q in exam selection.
# Enable topic-specific resume without clearing completed question stats.
source=source.replace("function save(){try{localStorage.setItem(KEY,JSON.stringify({stats,mistakes,bookmarks,history,session,lastResult}))}",
 "function save(){if(session&&session.mode==='study'&&session.label&&session.ids.length>1)topicSessions[session.label]=session;try{localStorage.setItem(KEY,JSON.stringify({stats,mistakes,bookmarks,history,session,lastResult,topicSessions}))}",1)
source=source.replace("let saved=load();let stats=", "let saved=load();let topicSessions=saved.topicSessions||{};let stats=",1)
source=source.replace("else if(a==='topic'){start(shuffled(Q.filter(q=>q.topic===e.dataset.topic)).map(q=>q.id),'study',0,e.dataset.topic)}",
 "else if(a==='topic'){let t=e.dataset.topic;if(session&&session.mode==='study'&&session.label===t){go('session')}else if(topicSessions[t]&&topicSessions[t].ids.every(id=>BYID[id])){if(session&&session.mode==='study'&&session.label)topicSessions[session.label]=session;session=topicSessions[t];save();go('session')}else{start(shuffled(Q.filter(q=>q.topic===t)).map(q=>q.id),'study',0,t)}}",1)
source=source.replace("function start(ids,mode='study',minutes=0,label=''){if(session", "function start(ids,mode='study',minutes=0,label=''){if(session",1)
# Make accurate totals dynamic rather than hardcoded 221 and 11.
source=source.replace("221 izstrādāts jautājums","\${Q.length} izstrādāts jautājums")
source=source.replace("<strong>221</strong>","<strong>\${Q.length}</strong>")
source=source.replace(" / 221</span>"," / \${Q.length}</span>")
source=source.replace("11 tematiskas sadaļas","\${TOPICS.length} tematiskas sadaļas")
# Do not leave the separately published addon as the primary entry.
index.write_text(source,encoding='utf-8')
print(f'Pages integrated {added} new questions; {len(data["questions"])} total, {len(set(q["topic"] for q in data["questions"]))} content topics')
