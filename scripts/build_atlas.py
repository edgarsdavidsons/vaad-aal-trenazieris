#!/usr/bin/env python3
"""Extract weed atlas photos, root diagrams and teacher-test images from materiali/.

Run locally (materiali/ is gitignored, so CI never runs this):
    python3 -m venv .venv && .venv/bin/pip install pymupdf pillow python-pptx
    .venv/bin/python scripts/build_atlas.py
Outputs committed files: assets/atlas/*.jpg and data/atlas.json.
"""
import io, json, re, unicodedata
from pathlib import Path
import pymupdf as fitz
from PIL import Image
from pptx import Presentation

root = Path(__file__).resolve().parents[1]
src = root / 'materiali'
out = root / 'assets' / 'atlas'
out.mkdir(parents=True, exist_ok=True)

GROUPS = {
    'efemera':      {'name': 'Efemērā', 'life': 'Īsmūža', 'desc': 'Īss attīstības cikls; vienā veģetācijas periodā var dot vairākas paaudzes.'},
    'agra_vasaras': {'name': 'Agrīnā vasaras', 'life': 'Īsmūža', 'desc': 'Vairojas ar sēklām, galvenokārt dīgst pavasarī.'},
    'vela_vasaras': {'name': 'Vēlīnā vasaras', 'life': 'Īsmūža', 'desc': 'Vairojas ar sēklām; pastiprināti dīgst tikai vasaras otrajā pusē un rudenī.'},
    'ziemotspejiga':{'name': 'Ziemotspējīgā', 'life': 'Īsmūža', 'desc': 'Sadīgstot rudenī, pārziemo rozetes stāvoklī; pavasara dīgsti attīstās kā vasaras nezāles, pārziemošana nav obligāta.'},
    'ziemas':       {'name': 'Ziemas', 'life': 'Īsmūža', 'desc': 'Dīgst rudenī; ziemošana sēklu ražošanai obligāta.'},
    'divgadiga':    {'name': 'Divgadīgā', 'life': 'Īsmūža', 'desc': 'Pirmajā gadā saknēs uzkrāj barības rezerves, otrajā zied un nogatavina sēklas.'},
    'barksaknu':    {'name': 'Bārkšsakņu', 'life': 'Daudzgadīgā', 'desc': 'Vairojas galvenokārt ar sēklām, iespējama arī veģetatīvā vairošanās; spēcīgas bārkšsaknes.'},
    'mietsaknu':    {'name': 'Mietsakņu', 'life': 'Daudzgadīgā', 'desc': 'Vairojas galvenokārt ar sēklām, iespējama arī veģetatīvā vairošanās; izteikta mietsakne.'},
    'saknenu':      {'name': 'Sakneņu', 'life': 'Daudzgadīgā', 'desc': 'Raksturīga veģetatīvā vairošanās ar sakneņiem (pazemes stumbriem ar pumpuriem).'},
    'saknu_dzinumu':{'name': 'Sakņu dzinumu', 'life': 'Daudzgadīgā', 'desc': 'Raksturīga veģetatīvā vairošanās ar dzinumiem no pumpuriem uz dziļām saknēm.'},
    'stigojosa':    {'name': 'Stīgojošā', 'life': 'Daudzgadīgā', 'desc': 'Vairojas ar virszemes stīgām, kas mezglos iesakņojas.'},
    'bumbulu':      {'name': 'Bumbuļu', 'life': 'Daudzgadīgā', 'desc': 'Vairojas ar bumbuļiem, kas atrodas sakņu galos.'},
    'sipolu':       {'name': 'Sīpolu', 'life': 'Daudzgadīgā', 'desc': 'Vairojas ar sīpoliem.'},
    'pusparazits':  {'name': 'Pusparazītiskā', 'life': 'Barošanās veids', 'desc': 'Pati fotosintezē, bet daļu ūdens un barības vielu iegūst no saimniekauga saknēm.'},
    'parazits':     {'name': 'Parazītiskā', 'life': 'Barošanās veids', 'desc': 'Bez hlorofila; visas barības vielas iegūst no saimniekauga.'},
}

# Root system / reproduction organ that the course asks about.
ROOTS = {
    'mietsakne_ism':  {'name': 'Mietsakne (īsmūža divdīgļlapji)', 'short': 'mietsakne', 'desc': 'Īsmūža divdīgļlapju nezālēm raksturīga mietsakne, vairāk vai mazāk zaraina. Balandai, zvērei, akļiem viegli izraujama; liektajam amarantam, sīkgalvītei, melnajai naktenei – stipri zaraina un dziļa.'},
    'barksaknes_ism': {'name': 'Bārkšsaknes (īsmūža viendīgļlapji)', 'short': 'bārkšsaknes', 'desc': 'Īsmūža viendīgļlapju (stiebrzāļu) nezālēm – plaši sazarota bārkšsakņu sistēma, kas spēcīgi saaug jau cerošanas fāzē (piem., parastā gaiļsāre).'},
    'barksaknes':     {'name': 'Bārkšsaknes (daudzgadīgās)', 'short': 'bārkšsaknes', 'desc': 'Daudzgadīgās bārkšsakņu nezāles veido spēcīgu bārkšsakņu sistēmu; vairojas galvenokārt ar sēklām.'},
    'mietsakne':      {'name': 'Mietsakne (daudzgadīgās)', 'short': 'mietsakne', 'desc': 'Daudzgadīgās mietsakņu nezāles – izteikta, bieži resna mietsakne ar barības vielu rezervēm; vairojas galvenokārt ar sēklām.'},
    'sakneni':        {'name': 'Sakneņi', 'short': 'sakneņi', 'desc': 'Sakneņi ir pazemes stumbri ar pumpuriem. Vārpatai tie ir aramkārtā (5–15 cm), māllēpei daudz dziļāk (0,8–1,0 m) vairākos stāvos.'},
    'saknu_dzinumi':  {'name': 'Sakņu dzinumi', 'short': 'sakņu dzinumi', 'desc': 'Jauni dzinumi veidojas no pumpuriem uz saknēm, kas parasti izvietotas ļoti dziļi (izņemot tīruma mīkstpieni).'},
    'stigas':         {'name': 'Virszemes stīgas', 'short': 'stīgas', 'desc': 'Ložņājoši virszemes dzinumi, kas mezglos iesakņojas; veido arī spēcīgas bārkšsaknes.'},
    'bumbuli':        {'name': 'Bumbuļi sakņu galos', 'short': 'bumbuļi', 'desc': 'Bumbuļu nezāles vairojas ar bumbuļiem, kas atrodas sakņu (pazemes dzinumu) galos.'},
    'sipoli':         {'name': 'Sīpoli', 'short': 'sīpoli', 'desc': 'Vairojas ar sīpoliem.'},
}
GROUP_ROOT = {'barksaknu': 'barksaknes', 'mietsaknu': 'mietsakne', 'saknenu': 'sakneni', 'saknu_dzinumu': 'saknu_dzinumi',
              'stigojosa': 'stigas', 'bumbulu': 'bumbuli', 'sipolu': 'sipoli'}

# name, page in Nezales_20220218.pdf, group, class (div/vien/spor), image indices on page (None=all), latin, extra
S = [
    ('Parastā virza', 9, 'efemera', 'div', None, 'Stellaria media'),
    ('Akļi', 11, 'agra_vasaras', 'div', None, 'Galeopsis spp.'),
    ('Ārstniecības matuzāle', 12, 'agra_vasaras', 'div', None, 'Fumaria officinalis'),
    ('Baltā balanda', 13, 'agra_vasaras', 'div', None, 'Chenopodium album'),
    ('Dārza mīkstpiene', 14, 'agra_vasaras', 'div', None, 'Sonchus oleraceus'),
    ('Dārza vējagriķis', 15, 'agra_vasaras', 'div', None, 'Fallopia convolvulus'),
    ('Izplestā balodene', 16, 'agra_vasaras', 'div', None, 'Atriplex patula'),
    ('Kodīgā nātre', 17, 'agra_vasaras', 'div', None, 'Urtica urens'),
    ('Ķeraiņu madara', 18, 'agra_vasaras', 'div', None, 'Galium aparine'),
    ('Maura kumelīte', 19, 'agra_vasaras', 'div', None, 'Matricaria discoidea'),
    ('Maura sūrene', 20, 'agra_vasaras', 'div', None, 'Polygonum aviculare'),
    ('Melnā naktene', 21, 'agra_vasaras', 'div', None, 'Solanum nigrum'),
    ('Parastā krustaine', 22, 'agra_vasaras', 'div', None, 'Senecio vulgaris'),
    ('Saules dievkrēsliņš', 23, 'agra_vasaras', 'div', None, 'Euphorbia helioscopia'),
    ('Sārtā panātre', 24, 'agra_vasaras', 'div', None, 'Lamium purpureum'),
    ('Sīkā gandrene', 25, 'agra_vasaras', 'div', None, 'Aethusa cynapium'),
    ('Skābeņlapu sūrene', 26, 'agra_vasaras', 'div', None, 'Persicaria lapathifolia'),
    ('Tīruma aitene', 27, 'agra_vasaras', 'div', None, 'Anchusa arvensis'),
    ('Tīruma gaurs', 28, 'agra_vasaras', 'div', None, 'Spergula arvensis'),
    ('Tīruma pavirza', 29, 'agra_vasaras', 'div', None, 'Anagallis arvensis'),
    ('Tīruma pērkone', 30, 'agra_vasaras', 'div', None, 'Raphanus raphanistrum'),
    ('Tīruma sinepe (zvēre)', 31, 'agra_vasaras', 'div', None, 'Sinapis arvensis'),
    ('Trejdaivu sunītis', 32, 'agra_vasaras', 'div', None, 'Bidens tripartita'),
    ('Airenes', 33, 'agra_vasaras', 'vien', None, 'Lolium spp.'),
    ('Maura skarene', 34, 'agra_vasaras', 'vien', None, 'Poa annua'),
    ('Vējauza', 35, 'agra_vasaras', 'vien', None, 'Avena fatua'),
    ('Liektais amarants', 37, 'vela_vasaras', 'div', None, 'Amaranthus retroflexus'),
    ('Sīkziedu sīkgalvīte', 38, 'vela_vasaras', 'div', None, 'Galinsoga parviflora'),
    ('Parastā gaiļsāre', 39, 'vela_vasaras', 'vien', None, 'Echinochloa crus-galli'),
    ('Zaļā sarene', 40, 'vela_vasaras', 'vien', None, 'Setaria viridis'),
    ('Lauka magone', 42, 'ziemotspejiga', 'div', None, 'Papaver dubium'),
    ('Ganu plikstiņš', 43, 'ziemotspejiga', 'div', None, 'Capsella bursa-pastoris'),
    ('Parastā grābeklīte', 44, 'ziemotspejiga', 'div', None, 'Erodium cicutarium'),
    ('Parastā pērkonene', 45, 'ziemotspejiga', 'div', None, 'Erysimum cheiranthoides'),
    ('Parastā rudzupuķe', 46, 'ziemotspejiga', 'div', None, 'Centaurea cyanus'),
    ('Parastā smalkžodzene', 47, 'ziemotspejiga', 'div', None, 'Descurainia sophia'),
    ('Tīruma ilzīte', 48, 'ziemotspejiga', 'div', None, 'Anthemis arvensis'),
    ('Tīruma kumelīte', 49, 'ziemotspejiga', 'div', None, 'Tripleurospermum inodorum'),
    ('Tīruma naudulis', 50, 'ziemotspejiga', 'div', None, 'Thlaspi arvense'),
    ('Tīruma neaizmirstulīte', 51, 'ziemotspejiga', 'div', None, 'Myosotis arvensis'),
    ('Tīruma veronika', 52, 'ziemotspejiga', 'div', None, 'Veronica arvensis'),
    ('Tīruma vijolīte', 53, 'ziemotspejiga', 'div', None, 'Viola arvensis'),
    ('Tīruma zilausis', 54, 'ziemotspejiga', 'div', None, 'Lithospermum arvense'),
    ('Parastā rudzusmilga', 55, 'ziemas', 'vien', [1, 2], 'Apera spica-venti'),
    ('Tīruma lāčauza', 55, 'ziemas', 'vien', [0], 'Bromus arvensis'),
    ('Austrumu dižpērkone', 57, 'divgadiga', 'div', [0], 'Bunias orientalis'),
    ('Ārstniecības vēršmēle', 57, 'divgadiga', 'div', [1], 'Anchusa officinalis'),
    ('Baltā spulgotne', 57, 'divgadiga', 'div', [2], 'Silene latifolia'),
    ('Parastā sirmene', 58, 'divgadiga', 'div', [0], 'Berteroa incana'),
    ('Savvaļas burkāns', 58, 'divgadiga', 'div', [1], 'Daucus carota'),
    ('Kodīgā gundega', 60, 'barksaknu', 'div', [0], 'Ranunculus acris'),
    ('Parastā brūngalvīte', 60, 'barksaknu', 'div', [1], 'Prunella vulgaris'),
    ('Lielā ceļteka', 61, 'barksaknu', 'div', None, 'Plantago major'),
    ('Ārstniecības pienene', 63, 'mietsaknu', 'div', [0], 'Taraxacum officinale'),
    ('Tīruma pēterene', 63, 'mietsaknu', 'div', [1], 'Knautia arvensis'),
    ('Cirtainā skābene', 64, 'mietsaknu', 'div', None, 'Rumex crispus'),
    ('Dzeltenā ilzīte', 65, 'mietsaknu', 'div', [0], 'Anthemis tinctoria'),
    ('Parastā pīpene', 65, 'mietsaknu', 'div', [1], 'Leucanthemum vulgare'),
    ('Šaurlapu ceļteka', 66, 'mietsaknu', 'div', None, 'Plantago lanceolata'),
    ('Vidējā ceļteka', 67, 'mietsaknu', 'div', None, 'Plantago media'),
    ('Baltā panātre', 69, 'saknenu', 'div', [0], 'Lamium album'),
    ('Parastais pelašķis', 69, 'saknenu', 'div', [1], 'Achillea millefolium'),
    ('Parastā gārsa', 70, 'saknenu', 'div', None, 'Aegopodium podagraria'),
    ('Parastā māllēpe', 71, 'saknenu', 'div', [0], 'Tussilago farfara'),
    ('Tīruma kosa', 71, 'saknenu', 'spor', [1], 'Equisetum arvense'),
    ('Parastā vībotne', 72, 'saknenu', 'div', None, 'Artemisia vulgaris'),
    ('Ložņu vārpata', 73, 'saknenu', 'vien', None, 'Elymus repens'),
    ('Lokaugļu zvērene', 75, 'saknu_dzinumu', 'div', [0], 'Erucastrum gallicum'),
    ('Parastā vīrcele', 75, 'saknu_dzinumu', 'div', [1], 'Linaria vulgaris'),
    ('Vīķi', 75, 'saknu_dzinumu', 'div', [2], 'Vicia spp.'),
    ('Mazā skābene', 76, 'saknu_dzinumu', 'div', None, 'Rumex acetosella'),
    ('Tīruma mīkstpiene', 77, 'saknu_dzinumu', 'div', None, 'Sonchus arvensis'),
    ('Tīruma tītenis', 78, 'saknu_dzinumu', 'div', None, 'Convolvulus arvensis'),
    ('Tīruma usne', 79, 'saknu_dzinumu', 'div', None, 'Cirsium arvense'),
    ('Ložņu gundega', 80, 'stigojosa', 'div', [0], 'Ranunculus repens'),
    ('Maura platkājiņš', 80, 'stigojosa', 'div', [1], 'Potentilla anserina'),
    ('Purva sārmene', 81, 'bumbulu', 'div', None, 'Stachys palustris'),
    ('Tīruma mētra', 82, 'bumbulu', 'div', None, 'Mentha arvensis'),
    ('Krūmāju sīpols', 83, 'sipolu', 'vien', None, 'Allium oleraceum'),
    ('Lielais zvagulis', 84, 'pusparazits', 'div', [0], 'Rhinanthus serotinus'),
    ('Parastais sārtžibulītis', 84, 'pusparazits', 'div', [1], 'Odontites vulgaris'),
    ('Linu vija', 84, 'parazits', 'div', [2], 'Cuscuta epilinum'),
]

# Notes that sharpen the root-system explanation for individual species.
ROOT_NOTES = {
    'Baltā balanda': 'Neliela, viegli izraujama mietsakne (Lapiņš, 39. att. A).',
    'Tīruma sinepe (zvēre)': 'Neliela, viegli izraujama mietsakne.',
    'Akļi': 'Neliela, viegli izraujama mietsakne.',
    'Skābeņlapu sūrene': 'Neliela, viegli izraujama mietsakne.',
    'Saules dievkrēsliņš': 'Neliela, viegli izraujama mietsakne.',
    'Parastā pērkonene': 'Neliela, viegli izraujama mietsakne.',
    'Liektais amarants': 'Jau dīgstu stadijā stipri zaraina, plaši un dziļi augsnē ejoša mietsakne.',
    'Sīkziedu sīkgalvīte': 'Jau dīgstu stadijā stipri zaraina, plaši un dziļi ejoša sakņu sistēma (Lapiņš, 39. att. B).',
    'Melnā naktene': 'Jau dīgstu stadijā stipri zaraina, plaši un dziļi ejoša sakņu sistēma.',
    'Parastā gaiļsāre': 'Plaši sazarota bārkšsakņu sistēma, kas spēcīgi saaug jau cerošanas fāzē (Lapiņš, 39. att. C).',
    'Ložņu vārpata': 'Sakneņi aramkārtā; viena auga sakneņi var izplatīties 3 m diametrā un veidot >200 dzinumu.',
    'Parastā māllēpe': 'Sakneņi izvietojas daudz dziļāk nekā vārpatai (0,8–1,0 m), vairākos horizontālos stāvos zem aramkārtas.',
    'Tīruma kosa': 'Sakneņi lien vertikāli un horizontāli (var būt vairākus metrus gari); vairojas arī ar sporām.',
    'Tīruma usne': 'Dziļa, vairākos horizontālos stāvos izvietota sakņu sistēma (līdz 5 m); jaunu augu var dot pat 3 mm sakņu fragments.',
    'Tīruma tītenis': 'Raksturīga dziļa mietsakne ar sakņu dzinumiem.',
    'Tīruma mīkstpiene': 'Vienīgā no sakņu dzinumu nezālēm, kuras saknes nav ļoti dziļi.',
    'Tīruma mētra': 'Vairojas ar bumbuļiem sakņu galos.',
    'Ložņu gundega': 'Vairojas ar virszemes stīgām; veido arī spēcīgas bārkšsaknes.',
    'Maura platkājiņš': 'Vairojas ar virszemes stīgām; veido arī spēcīgas bārkšsaknes.',
}


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '_', s).strip('_')


def save(im, name, maxw=560, quality=72):
    im = im.convert('RGB')
    if im.width > maxw:
        im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    path = out / f'{name}.jpg'
    im.save(path, 'JPEG', quality=quality, optimize=True, progressive=True)
    return f'assets/atlas/{name}.jpg'


def page_images(doc, pn):
    """Content images of a page ordered by position (top-to-bottom, left-to-right), background excluded."""
    p = doc[pn - 1]
    found = []
    for im in p.get_images(full=True):
        x = doc.extract_image(im[0])
        if (x['width'], x['height']) == (842, 595):
            continue
        for r in p.get_image_rects(im[0]):
            found.append((r, Image.open(io.BytesIO(x['image']))))
    # Assign order: images whose top edge is within 60pt are one "row"; sort by x within a row.
    found.sort(key=lambda t: (round(t[0].y0 / 120), t[0].x0))
    return found


def by_x(doc, pn):
    imgs = page_images(doc, pn)
    imgs.sort(key=lambda t: t[0].x0)
    return imgs


doc = fitz.open(src / 'Copy of Nezales_20220218.pdf')
BY_X_PAGES = {58, 60, 63, 65, 69, 71, 80, 84}
species = []
for name, pn, group, cls, idx, latin in S:
    if pn == 55:
        imgs = sorted(page_images(doc, pn), key=lambda t: -t[0].x0)  # right-most = lāčauza
        imgs = [imgs[0]] + sorted(imgs[1:], key=lambda t: t[0].x0)
    elif pn in (57, 75):
        imgs = sorted(page_images(doc, pn), key=lambda t: (t[0].y0 > 300, t[0].x0))
    elif pn in BY_X_PAGES:
        imgs = by_x(doc, pn)
    else:
        imgs = page_images(doc, pn)
    chosen = imgs if idx is None else [imgs[i] for i in idx]
    paths = [save(im, f'{slug(name)}_{i + 1}') for i, (_, im) in enumerate(chosen)]
    item = dict(id=slug(name), name=name, latin=latin, group=group,
                cls={'div': 'divdīgļlapis', 'vien': 'viendīgļlapis', 'spor': 'sporaugs'}[cls], images=paths)
    if group in GROUP_ROOT:
        item['root'] = GROUP_ROOT[group]
    elif GROUPS[group]['life'] == 'Īsmūža':
        item['root'] = 'barksaknes_ism' if cls == 'vien' else 'mietsakne_ism'
    if name in ROOT_NOTES:
        item['rootNote'] = ROOT_NOTES[name]
    species.append(item)

# Lapiņš (2021) root diagrams. Captions at the bottom are cropped so they do not reveal answers.
figs = []
for pn, fig, crop_bottom, labels in [
    (85, 'fig39', 0.115, {'A': 'Baltā balanda', 'B': 'Sīkziedu sīkgalvīte', 'C': 'Parastā gaiļsāre'}),
    (86, 'fig40', 0.10, {'': 'Ložņu vārpata'}),
    (87, 'fig41', 0.075, {'A': 'Tīruma mīkstpiene', 'B': 'Parastā māllēpe'}),
    (88, 'fig42', 0.085, {'A': 'Tīruma usne', 'B': 'Tīruma tītenis', 'C': 'Tīruma kosa', 'D': 'Tīruma mīkstpiene', 'E': 'Ložņu vārpata'}),
    (89, 'fig43', 0.09, {'': 'Tīruma mētra'}),
]:
    (_, im), = page_images(doc, pn)
    im = im.convert('RGB')
    im = im.crop((0, 0, im.width, round(im.height * (1 - crop_bottom))))
    figs.append(dict(id=fig, image=save(im, f'root_{fig}', maxw=720, quality=80), labels=labels))

# Teacher's Google Forms test: crop question images from the long screenshot.
form = fitz.open(next(src.glob('screencapture-docs-google-forms-*.pdf')))
p0 = form[0]
tiles = [Image.open(io.BytesIO(form.extract_image(i[0])['image'])).convert('RGB') for i in p0.get_images()]
full = Image.new('RGB', (tiles[0].width, sum(t.height for t in tiles)), 'white')
y = 0
for t in tiles:
    full.paste(t, (0, y)); y += t.height
# Coordinates are in the 0.55-scaled preview of the centre column (x offset 25 %).
K = 0.55
X0 = full.width * 0.25
TEST_BOXES = {
    1: (150, 462, 525, 708), 2: (150, 1018, 680, 1318), 3: (150, 1640, 560, 1880),
    4: (150, 2236, 623, 2552), 5: (150, 2852, 442, 3436), 6: (150, 3702, 592, 4070),
    7: (150, 4410, 601, 4709), 8: (150, 5008, 662, 5384), 10: (150, 6016, 568, 6539),
    11: (150, 6855, 530, 7119), 12: (150, 7378, 555, 7886), 13: (150, 8240, 634, 8631),
    14: (150, 8958, 608, 9303), 15: (150, 9604, 487, 10055), 16: (150, 10381, 702, 10678),
    17: (150, 10978, 598, 11669), 18: (150, 12048, 437, 12486), 21: (150, 13366, 397, 13690),
}
test_images = {}
for q, (x1, y1, x2, y2) in TEST_BOXES.items():
    box = (round(X0 + x1 / K), round(y1 / K), round(X0 + x2 / K), round(y2 / K))
    test_images[str(q)] = save(full.crop(box), f'test_q{q:02d}', maxw=720, quality=78)

# Selected, unambiguous photos from nezāles.pptx (slide_shape -> label).
pptx_pick = {
    (4, 5): ('pp_dratstarps', 'Drātstārps – sprakšķu (sprakšķvaboļu) kāpurs'),
    (4, 4): ('pp_rusa', 'Labību rūsa uz lapas'),
    (8, 2): ('pp_kosa_sporas', 'Tīruma kosas pavasara sporu vārpas'),
    (19, 2): ('pp_varpata_saknenis', 'Ložņu vārpatas sakneņi'),
    (22, 2): ('pp_usne_saknes', 'Tīruma usnes sakņu sistēma augsnē'),
    (22, 3): ('pp_usne_dzinumi', 'Tīruma usnes sakņu dzinumi'),
    (18, 3): ('pp_titenis', 'Tīruma tītenis ziedos'),
    (27, 1): ('pp_vejauza', 'Vējauzas skaras'),
    (29, 1): ('pp_gailsare', 'Parastās gaiļsāres skara'),
    (31, 4): ('pp_lacauza', 'Lāčauzas vārpiņas'),
    (25, 2): ('pp_veronika', 'Veronika ziedā'),
    (19, 6): ('pp_virza', 'Parastā virza ziedā'),
}
pres = Presentation(src / 'Copy of nezāles.pptx')
pptx_images = {}
for si, slide in enumerate(pres.slides, 1):
    for j, shape in enumerate(slide.shapes):
        if (si, j) in pptx_pick and shape.shape_type == 13:
            key, label = pptx_pick[(si, j)]
            pptx_images[key] = dict(image=save(Image.open(io.BytesIO(shape.image.blob)), key), label=label)

atlas = dict(groups=GROUPS, roots=ROOTS, species=species, rootFigures=figs, testImages=test_images, extraImages=pptx_images)
(root / 'data' / 'atlas.json').write_text(json.dumps(atlas, ensure_ascii=False, indent=1), encoding='utf-8')
total = sum(f.stat().st_size for f in out.glob('*.jpg'))
print(f'{len(species)} species, {sum(len(s["images"]) for s in species)} photos, {len(figs)} root figures, '
      f'{len(test_images)} test images, {len(pptx_images)} pptx images; {total / 1e6:.1f} MB')
