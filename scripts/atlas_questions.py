"""Generate weed-atlas questions (photos, root systems, biological groups, teacher test, booklet facts).

Used by merge_questions.py. Input files are committed: data/atlas.json, data/teacher_test.json,
data/booklet_questions.json and assets/atlas/*.jpg (produced locally by build_atlas.py).
Generation is seeded, so question IDs and option sets stay stable between builds and saved progress keeps working.
"""
import json, random
from pathlib import Path

T_PHOTO = 'Nezāļu foto atlants'
T_ROOT = 'Sakņu sistēmas ↔ augi'
T_GROUP = 'Bioloģiskās grupas'
T_BOOK = 'Nezāļu bukleti'
TOPICS = [(T_PHOTO, '📸'), (T_ROOT, '🌱'), (T_GROUP, '🧬'), (T_BOOK, '📘')]

SOURCES = {
    'ATLAS': {'title': 'D. Piliksere. Izplatītākās nezāles augkopībā (2022), foto: Hamouz, Bayer, latvijasdaba.lv', 'url': 'https://www.arei.lv/', 'type': 'Nezāļu atlants'},
    'LAPINS': {'title': 'D. Lapiņš (2021) nezāļu sakņu sistēmu attēli', 'url': 'https://www.arei.lv/', 'type': 'Sakņu shēma'},
    'TEST': {'title': 'Skolotājas Google Forms „Nezāļu tests”', 'url': '#', 'type': 'Skolotājas tests (Google Forms)'},
    'BOOK': {'title': 'Latvijā izplatītākās nezāles (bukleti 2016, 2017) un kursa prezentācijas', 'url': 'https://www.arei.lv/', 'type': 'Buklets'},
}

# Group pairs that different course materials classify differently – never offer them side by side.
CONFLICTS = {('ziemas', 'ziemotspejiga'), ('efemera', 'agra_vasaras')}
# Species whose group differs between course materials – no group questions for them.
GROUP_AMBIGUOUS = {'Sārtā panātre', 'Maura skarene', 'Parastā virza'}
# Plants that also show the trait of another root group – not usable as distractors for that group.
ALSO_HAS = {'barksaknes': {'Ložņu gundega', 'Maura platkājiņš'}, 'mietsakne': {'Tīruma tītenis'}}


def lower_first(s):
    return s[:1].lower() + s[1:]


def build(data, root):
    root = Path(root)
    atlas = json.loads((root / 'data/atlas.json').read_text(encoding='utf-8'))
    teacher = json.loads((root / 'data/teacher_test.json').read_text(encoding='utf-8'))
    booklet = json.loads((root / 'data/booklet_questions.json').read_text(encoding='utf-8'))
    rng = random.Random(20261029)
    groups, roots, species = atlas['groups'], atlas['roots'], atlas['species']
    by_name = {s['name']: s for s in species}
    images = data['images']
    data['sources'].update(SOURCES)
    questions = []

    def img(path):
        key = 'atlas/' + Path(path).stem
        images[key] = path
        return key

    def add(qid, topic, q, correct, wrong, why, source, image=None):
        wrong = [w for w in dict.fromkeys(wrong) if w != correct][:3]
        assert len(wrong) == 3, (qid, correct, wrong)
        item = dict(id=qid, topic=topic, q=q, opts=[correct, *wrong], why=why, source=source)
        if image:
            item['image'] = image
        questions.append(item)

    def members(rid):
        return [s['name'] for s in species if s.get('root') == rid]

    def group_line(s):
        g = groups[s['group']]
        return f"{g['life']} – {g['name'].lower()} nezāle" if g['life'] != 'Barošanās veids' else g['name'] + ' nezāle'

    def root_line(rid):
        names = members(rid)
        return f"{roots[rid]['name']}: {', '.join(names)}."

    def describe(s):
        parts = [f"{s['name']} ({s['latin']}) – {s['cls']}; {group_line(s)}."]
        if s.get('root'):
            parts.append(f"Sakņu sistēma: {roots[s['root']]['short']}." + (' ' + s['rootNote'] if s.get('rootNote') else ''))
        return ' '.join(parts)

    # 1. Photo identification – distractors from the same group first, then the same life form.
    for s in species:
        same_group = [o['name'] for o in species if o['group'] == s['group'] and o is not s]
        same_life = [o['name'] for o in species if groups[o['group']]['life'] == groups[s['group']]['life'] and o is not s]
        for n, path in enumerate(s['images'][:2], 1):
            pool = rng.sample(same_group, min(2, len(same_group)))
            rest = [x for x in same_life if x not in pool]
            pool += rng.sample(rest, min(3, len(rest)))
            pool += rng.sample([o['name'] for o in species if o is not s and o['name'] not in pool], 3)
            add(f"ATF-{s['id']}-{n}", T_PHOTO, 'Kura nezāle redzama attēlā?' if n == 1 else 'Nezāli sauc', s['name'],
                pool, describe(s), 'ATLAS', img(path))

    # 2. Plant → root system. Distractors exclude organs the plant also has (e.g. tītenis has a taproot).
    perennial_roots = ['barksaknes', 'mietsakne', 'sakneni', 'saknu_dzinumi', 'stigas', 'bumbuli', 'sipoli']
    for s in species:
        rid = s.get('root')
        if not rid:
            continue
        note = s.get('rootNote', '').lower()
        candidates = perennial_roots + ['mietsakne_ism', 'barksaknes_ism']
        candidates = [r for r in candidates if r != rid and roots[r]['short'] != roots[rid]['short']
                      and roots[r]['short'] not in note and not (r.startswith('mietsakne') and 'mietsakne' in note)
                      and not (r.startswith('barksaknes') and 'bārkšsaknes' in note)]
        if rid.endswith('_ism'):  # short-lived: show the other short-lived type + perennial organs
            other = 'barksaknes_ism' if rid == 'mietsakne_ism' else 'mietsakne_ism'
            wrong = [other] + rng.sample([r for r in candidates if r in perennial_roots and r not in ('mietsakne', 'barksaknes')], 2)
        else:
            wrong = rng.sample([r for r in candidates if not r.endswith('_ism')], 3)
        add(f"ATR-{s['id']}", T_ROOT, f"Kāda sakņu sistēma vai vairošanās orgāns raksturīgs nezālei „{lower_first(s['name'])}”?",
            roots[rid]['name'], [roots[r]['name'] for r in wrong],
            f"{describe(s)} {root_line(rid)}", 'ATLAS', img(s['images'][-1]) if not rid.endswith('_ism') else None)

    # 3. Root system → plant (every member of each perennial group once; sample of the big short-lived groups).
    ask = {
        'barksaknes': 'Kura no šīm daudzgadīgajām nezālēm pieder pie bārkšsakņu nezālēm?',
        'mietsakne': 'Kura no šīm daudzgadīgajām nezālēm pieder pie mietsakņu nezālēm?',
        'sakneni': 'Kura no šīm nezālēm vairojas ar sakneņiem?',
        'saknu_dzinumi': 'Kura no šīm nezālēm vairojas ar sakņu dzinumiem?',
        'stigas': 'Kura no šīm nezālēm vairojas ar virszemes stīgām?',
        'bumbuli': 'Kura no šīm nezālēm vairojas ar bumbuļiem sakņu galos?',
        'sipoli': 'Kura no šīm nezālēm vairojas ar sīpoliem?',
        'barksaknes_ism': 'Kura no šīm ir īsmūža viendīgļlapju nezāle ar bārkšsakņu sistēmu?',
        'mietsakne_ism': 'Kura no šīm ir īsmūža divdīgļlapju nezāle ar mietsakni?',
    }
    for rid, question in ask.items():
        names = members(rid)
        if rid == 'mietsakne_ism':
            names = rng.sample(names, 12)
        if rid.endswith('_ism'):
            others = [s['name'] for s in species if s.get('root') and not s['root'].endswith('_ism')]
            if rid == 'barksaknes_ism':
                others += members('mietsakne_ism')
        else:
            others = [s['name'] for s in species if s.get('root') and s['root'] != rid and s['name'] not in ALSO_HAS.get(rid, ())]
        for name in names:
            add(f"ATQ-{rid}-{by_name[name]['id']}", T_ROOT, question, name, rng.sample(others, 3),
                f"{roots[rid]['desc']} {root_line(rid)}", 'ATLAS')

    # 4. "Which one does NOT belong" – teaches complete member lists of the perennial groups.
    for rid in ['barksaknes', 'mietsakne', 'sakneni', 'saknu_dzinumi']:
        names = members(rid)
        outsiders = [s['name'] for s in species if s.get('root') and s['root'] != rid and not s['root'].endswith('_ism')
                     and s['name'] not in ALSO_HAS.get(rid, ())]
        for k in range(3):
            inside = rng.sample(names, 3)
            odd = rng.choice(outsiders)
            add(f"ATN-{rid}-{k + 1}", T_ROOT, f"Kura no šīm nezālēm NEPIEDER grupai „{roots[rid]['name']}”?", odd, inside,
                f"{odd} – {roots[by_name[odd]['root']]['name'].lower()}. {root_line(rid)}", 'ATLAS')

    # 5. Lapiņš (2021) diagrams in the teacher's format.
    figs = {f['id']: f for f in atlas['rootFigures']}
    f39, f40, f41, f42, f43 = (img(figs[k]['image']) for k in ['fig39', 'fig40', 'fig41', 'fig42', 'fig43'])
    why39 = 'D. Lapiņa 39. att.: A – baltā balanda (neliela, viegli izraujama mietsakne), B – sīkziedu sīkgalvīte (stipri zaraina, dziļa mietsakne), C – parastā gaiļsāre (bārkšsaknes, spēcīgi saaug jau cerošanas fāzē).'
    why42 = 'D. Lapiņa 42. att.: A – tīruma usne (dziļa, vairākos horizontālos stāvos), B – tīruma tītenis (dziļa mietsakne), C – tīruma kosa (sakneņi un sporas), D – tīruma mīkstpiene (sakņu dzinumi, seklāk), E – ložņu vārpata (sakneņi aramkārtā).'
    why41 = 'D. Lapiņa 41. att.: A – tīruma mīkstpiene (sakņu dzinumi), B – parastā māllēpe (sakneņi 0,8–1,0 m dziļumā, vairākos stāvos zem aramkārtas).'
    fig_q = [
        ('fig39-1', f39, 'Attēlā redzamās sakņu sistēmas A, B un C pieder', 'A baltajai balandai, B sīkziedu sīkgalvītei, C parastajai gaiļsārei',
         ['A parastajai gaiļsārei, B baltajai balandai, C sīkziedu sīkgalvītei', 'A tīruma usnei, B tīruma tītenim, C tīruma kosai', 'A sīkziedu sīkgalvītei, B parastajai gaiļsārei, C baltajai balandai'], why39),
        ('fig39-2', f39, 'Baltajai balandai pieder sakne', 'A attēlā', ['B attēlā', 'C attēlā', 'Neviena no attēlā redzamajām'], why39),
        ('fig39-3', f39, 'Sīkziedu sīkgalvītei (galinsogai) pieder sakne', 'B attēlā', ['A attēlā', 'C attēlā', 'Neviena no attēlā redzamajām'], why39),
        ('fig39-4', f39, 'Kura attēlā redzamā sakņu sistēma raksturīga viendīgļlapjiem?', 'C – bārkšsaknes', ['A – mietsakne', 'B – zaraina mietsakne', 'Visas trīs'], why39),
        ('fig40-1', f40, 'Attēlā ar cipariem 1, 2, 3 apzīmēti šīs nezāles pazemes stumbri (sakneņi). Tā ir', 'ložņu vārpata', ['tīruma usne', 'tīruma tītenis', 'ložņu gundega'],
         'D. Lapiņa 40. att.: ložņu vārpatas sakneņi aramkārtā. Sakneņi ir pazemes vasas pārveidnes ar pumpuriem.'),
        ('fig40-2', f40, 'Attēlā redzamajai nezālei pazemē ir', 'sakneņi', ['sakņu dzinumi no dziļām saknēm', 'bumbuļi sakņu galos', 'mietsakne'],
         'D. Lapiņa 40. att.: ložņu vārpatas sakneņi – pazemes stumbri ar mezgliem un pumpuriem; atrodas aramkārtā.'),
        ('fig41-1', f41, 'Attēlā redzamās sakņu sistēmas pieder', 'A tīruma mīkstpienei, B parastajai māllēpei',
         ['A parastajai māllēpei, B tīruma mīkstpienei', 'A ložņu vārpatai, B tīruma usnei', 'A tīruma mētrai, B ārstniecības pienenei'], why41),
        ('fig41-2', f41, 'Kura nezāle attēlā B veido sakneņus daudz dziļāk nekā vārpata (0,8–1,0 m)?', 'parastā māllēpe',
         ['tīruma mīkstpiene', 'ložņu vārpata', 'tīruma kosa'], why41),
        ('fig42-1', f42, 'Kurai nezālei pieder attēlā D redzamā sakņu sistēma?', 'tīruma mīkstpienei', ['tīruma usnei', 'tīruma kosai', 'ložņu vārpatai'], why42),
        ('fig42-2', f42, 'Kura no attēlā redzamajām sakņu sistēmām atrodas sekli, aramkārtā (E)?', 'ložņu vārpatai', ['tīruma usnei', 'tīruma tītenim', 'tīruma kosai'], why42),
        ('fig42-3', f42, 'Attēlā A redzamā nezāle veido dziļu, vairākos horizontālos stāvos izvietotu sakņu sistēmu. Tā ir', 'tīruma usne',
         ['tīruma kosa', 'ložņu vārpata', 'tīruma mīkstpiene'], why42),
        ('fig42-4', f42, 'Attēlā B redzamajai nezālei raksturīga dziļa mietsakne ar sakņu dzinumiem. Tā ir', 'tīruma tītenis',
         ['tīruma usne', 'ārstniecības pienene', 'tīruma mīkstpiene'], why42),
        ('fig43-1', f43, 'Šī daudzgadīgā nezāle vairojas ar bumbuļiem, kas atrodas sakņu galos. Tā ir', 'tīruma mētra',
         ['ložņu vārpata', 'tīruma mīkstpiene', 'tīruma usne'], 'D. Lapiņa 43. att.: tīruma mētra – bumbuļu nezāle. Pie bumbuļu nezālēm pieder arī purva sārmene.'),
    ]
    for qid, image, q, correct, wrong, why in fig_q:
        add(f'ATD-{qid}', T_ROOT, q, correct, wrong, why, 'LAPINS', image)

    # 6. Biological group of short-lived weeds; life form + class from a photo (teacher question 21 format).
    short_groups = [g for g, v in groups.items() if v['life'] == 'Īsmūža']
    for s in species:
        if groups[s['group']]['life'] != 'Īsmūža' or s['name'] in GROUP_AMBIGUOUS:
            continue
        wrong = [g for g in short_groups if g != s['group'] and (s['group'], g) not in CONFLICTS and (g, s['group']) not in CONFLICTS]
        add(f"ATG-{s['id']}", T_GROUP, f"Pie kuras īsmūža nezāļu bioloģiskās grupas pieder „{lower_first(s['name'])}”?",
            groups[s['group']]['name'], [groups[g]['name'] for g in rng.sample(wrong, 3)],
            f"{describe(s)} {groups[s['group']]['name']}: {groups[s['group']]['desc']}", 'ATLAS')
    life_cls = ['īsmūža divdīgļlapis', 'īsmūža viendīgļlapis', 'daudzgadīgs divdīgļlapis', 'daudzgadīgs viendīgļlapis']
    for s in species:
        life = groups[s['group']]['life']
        if s['cls'] == 'sporaugs' or life == 'Barošanās veids':
            continue
        correct = ('īsmūža ' if life == 'Īsmūža' else 'daudzgadīgs ') + s['cls']
        add(f"ATC-{s['id']}", T_GROUP, 'Attēlā redzamā nezāle ir', correct, [x for x in life_cls if x != correct],
            describe(s), 'ATLAS', img(s['images'][-1]))

    # 7. Teacher's Google Forms questions, mixed into the matching topics (not a separate section).
    for t in teacher:
        image = img(atlas['testImages'][str(t['n'])]) if str(t['n']) in atlas['testImages'] else None
        add(f"TT{t['n']:02d}", t['topic'], t['q'], t['opts'][0], t['opts'][1:], t['why'], 'TEST', image)

    # 8. Booklet facts.
    extra = atlas['extraImages']
    for n, b in enumerate(booklet, 1):
        add(f'BK{n:03d}', T_BOOK, b['q'], b['opts'][0], b['opts'][1:], b['why'], 'BOOK',
            img(extra[b['image']]['image']) if b.get('image') else None)

    # Atlas reference data for the in-app atlas view (image keys resolve through DATA.images).
    data['atlas'] = dict(
        groups=groups, roots=roots,
        species=[dict(s, images=[img(p) for p in s['images']]) for s in species],
        rootFigures=[dict(f, image=img(f['image'])) for f in atlas['rootFigures']],
        extra=[dict(label=v['label'], image=img(v['image'])) for v in extra.values()],
    )
    for path in images.values():
        if path.startswith('assets/'):
            assert (root / path).is_file(), f'Missing atlas image {path}'
    return questions
