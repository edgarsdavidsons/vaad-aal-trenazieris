"""Searchable knowledge base over everything in the trainer.

Reads the built index.html (questions, weed atlas, root systems, sources) and
data/mk950_text.txt (full text of MK noteikumi Nr. 950). Used by mcp_server.py and ask.py.
No third-party dependencies.
"""
import json, random, re, unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

root = Path(__file__).resolve().parents[1]
MK950_URL = 'https://likumi.lv/ta/id/241853-augu-aizsardzibas-lidzeklu-lietosanas-noteikumi'


def fold(text):
    """Lower-case and strip Latvian diacritics so 'nezāle' matches 'nezale'."""
    text = unicodedata.normalize('NFKD', str(text).casefold())
    return ''.join(c for c in text if not unicodedata.combining(c))


def stems(text):
    # Latvian is heavily inflected: comparing the first 5 letters of each word
    # matches 'nezāles', 'nezālēm', 'nezāļu' well enough without a stemmer.
    return [w[:5] for w in re.findall(r'[a-z0-9]+', fold(text)) if len(w) >= 3 or w.isdigit()]


@lru_cache(maxsize=1)
def app_data():
    page = (root / 'index.html').read_text(encoding='utf-8')
    m = re.search(r'<script type="application/json" id="app-data">(.*?)</script>', page, re.S)
    if not m:
        raise RuntimeError('index.html has no app-data JSON; run scripts/merge_questions.py')
    return json.loads(m.group(1).replace('<\\/', '</'))


@lru_cache(maxsize=1)
def mk950_points():
    """Split the regulation into numbered points: {'18.1': '18.1. augus drīkst ...', ...}."""
    points, current = {}, None
    for line in (root / 'data/mk950_text.txt').read_text(encoding='utf-8').splitlines():
        line = line.strip()
        # '21.1. sēklas kodina' is sub-point 21.1; '21.1 Pirmās ...' is the inserted point 21¹.
        m = re.match(r'^(\d+(?:\.\d+)*)(\.\s|\s(?=[A-ZĀČĒĢĪĶĻŅŠŪŽ]))', line)
        if m:
            current = m.group(1) if m.group(2).startswith('.') else m.group(1).replace('.1', '¹')
            points[current] = line
        elif current and line:
            points[current] += '\n' + line
    return points


def question_public(q, with_answer=True):
    data = app_data()
    src = data['sources'].get(q.get('source'), {})
    item = dict(id=q['id'], topic=q['topic'], question=q['q'])
    if with_answer:
        item.update(correct_answer=q['opts'][0], wrong_options=q['opts'][1:], explanation=q.get('why', ''))
    else:
        item['options'] = random.sample(q['opts'], len(q['opts']))
    item['has_image'] = bool(q.get('image'))
    item['source'] = src.get('title', q.get('source', ''))
    return item


@lru_cache(maxsize=1)
def documents():
    """Every searchable piece of content as (kind, id, title, text, payload)."""
    data = app_data()
    docs = []
    for q in data['questions']:
        text = f"{q['q']} {q['opts'][0]} {q.get('why', '')} {q['topic']}"
        docs.append(('question', q['id'], q['q'], text, q))
    atlas = data.get('atlas', {})
    groups, roots = atlas.get('groups', {}), atlas.get('roots', {})
    for sp in atlas.get('species', []):
        g, r = groups.get(sp.get('group'), {}), roots.get(sp.get('root'), {})
        info = dict(name=sp['name'], latin=sp.get('latin'), class_=sp.get('cls'),
                    biological_group=g.get('name'), group_description=g.get('desc'),
                    life=g.get('life'), root_system=r.get('name'), root_description=r.get('desc'))
        docs.append(('weed', sp['id'], sp['name'], ' '.join(str(v) for v in info.values() if v), info))
    for key, g in groups.items():
        members = [s['name'] for s in atlas.get('species', []) if s.get('group') == key]
        info = dict(group=g['name'], life=g.get('life'), description=g.get('desc'), weeds=members)
        docs.append(('biological_group', key, g['name'], f"{g['name']} bioloģiskā grupa {g.get('desc', '')}", info))
    for key, r in roots.items():
        members = [s['name'] for s in atlas.get('species', []) if s.get('root') == key]
        info = dict(root_system=r['name'], description=r.get('desc'), weeds=members)
        docs.append(('root_system', key, r['name'], f"{r['name']} sakņu sistēma {r.get('desc', '')}", info))
    for rt in data.get('rootTypes', []):
        docs.append(('root_type', rt['id'], rt['name'], ' '.join(str(v) for v in rt.values()), rt))
    for w in data.get('weeds', []):
        docs.append(('weed_photo', str(w['id']), w['name'], w.get('detail', w['name']), dict(name=w['name'], detail=w.get('detail'))))
    for num, text in mk950_points().items():
        docs.append(('mk950_point', num, f'MK Nr. 950, {num}. punkts', text,
                     dict(point=num, text=text, url=MK950_URL)))
    return [(kind, did, title, text, payload, Counter(stems(text)), Counter(stems(title))) for kind, did, title, text, payload in docs]


def search(query, kinds=None, limit=10):
    terms = set(stems(query))
    if not terms:
        return []
    hits = []
    for kind, did, title, text, payload, body, head in documents():
        if kinds and kind not in kinds:
            continue
        matched = [t for t in terms if t in body]
        if not matched:
            continue
        # Coverage of the query matters most; title hits and rare-term frequency break ties.
        score = len(matched) / len(terms) * 10 + sum(t in head for t in matched) + min(sum(body[t] for t in matched), 5) * 0.1
        hits.append((score, kind, did, title, payload))
    hits.sort(key=lambda h: -h[0])
    out = []
    for score, kind, did, title, payload in hits[:limit]:
        if kind == 'question':
            payload = question_public(payload)
        out.append(dict(kind=kind, id=did, title=title, score=round(score, 2), content=payload))
    return out


def topics():
    counts = Counter(q['topic'] for q in app_data()['questions'])
    return [dict(topic=t, questions=n) for t, n in counts.most_common()]


def topic_questions(topic, limit=50, offset=0):
    qs = [q for q in app_data()['questions'] if fold(q['topic']) == fold(topic)]
    return dict(topic=topic, total=len(qs), questions=[question_public(q) for q in qs[offset:offset + limit]])


def get_question(qid):
    for q in app_data()['questions']:
        if q['id'] == qid:
            return question_public(q)
    return None


def quiz(topic=None, count=5):
    qs = app_data()['questions']
    if topic:
        qs = [q for q in qs if fold(q['topic']) == fold(topic)]
    qs = [q for q in qs if not q.get('image')]  # photo questions need the web page
    return [question_public(q, with_answer=False) for q in random.sample(qs, min(count, len(qs)))]


def check_answer(qid, answer):
    q = next((q for q in app_data()['questions'] if q['id'] == qid), None)
    if not q:
        return None
    return dict(id=qid, correct=fold(answer).strip() == fold(q['opts'][0]).strip(),
                correct_answer=q['opts'][0], explanation=q.get('why', ''))


def mk950_point(point):
    """Point '18' returns 18 and its sub-points; inserted points are written '13¹' (or '13^1')."""
    pts = mk950_points()
    point = point.strip().rstrip('.').replace('^1', '¹')
    found = {k: v for k, v in pts.items() if k == point or k.startswith(point + '.')}
    return dict(url=MK950_URL, points=found) if found else None


def overview():
    data = app_data()
    return dict(questions=len(data['questions']), topics=len(topics()),
                atlas_weeds=len(data.get('atlas', {}).get('species', [])),
                mk950_points=len(mk950_points()),
                sources=[dict(code=k, **v) for k, v in data['sources'].items()])
