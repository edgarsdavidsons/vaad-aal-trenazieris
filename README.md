# VAAD AAL 2. reģistrācijas klases eksāmena trenažieris

Tīmekļa trenažieris sagatavošanās mācībām augu aizsardzības līdzekļu (AAL) lietotāju zināšanu pārbaudei.

## Atvērt trenažieri
Kad aktivizēts GitHub Pages: https://edgarsdavidsons.github.io/vaad-aal-trenazieris/

## Iespējas
- Galvenā jautājumu banka tiek papildināta automātiski no kursa un praktisko uzdevumu datiem; ietver attēlu atpazīšanu, marķējumu analīzi, aprēķinus un situāciju uzdevumus.
- Mācību režīms pa tēmām, eksāmena simulācija un kļūdu atkārtošana.
- Atbilžu skaidrojumi, rezultātu vēsture, progresa pārskats.
- Progress glabājas atsevišķi katra lietotāja pārlūkā (localStorage); konts nav nepieciešams.
- Mobilajām ierīcēm pielāgota saskarne; treniņam bezsaistē var lejupielādēt `index.html`.

## Izvietošana GitHub Pages
Atveriet `Settings → Pages → Build and deployment`, izvēlieties `Deploy from a branch`, `main`, `/(root)`, un nospiediet `Save`.

## Svarīgi
Šis ir **neatkarīgs trenažieris**, nevis VAAD oficiālais eksāmens vai oficiālo eksāmena jautājumu banka. Simulācijas jautājumu skaits un laika limits nav apstiprināts VAAD formāts. AAL faktiskai lietošanai pārbaudiet spēkā esošo marķējumu, VAAD reģistru un normatīvo regulējumu.

Trenažierī ietverti arī attēli no mācību materiāliem. Pirms to tālākas pārpublicēšanas vai komerciālas izmantošanas jāpārliecinās par atbilstošajām izmantošanas tiesībām.

Oficiālā VAAD programma: https://www.vaad.gov.lv/lv/otras-registracijas-klases-aal-lietotaju-macibas-apraksts-un-programma

## Galvenā trenažiera papildinājumi

Visi jauno tēmu jautājumi tiek integrēti [galvenajā trenažierī](https://edgarsdavidsons.github.io/vaad-aal-trenazieris/) izvietošanas laikā.

- 122 papildu jautājumi 10 tēmās, veidoti no VAAD kursa Google Drive materiāliem (nezāles, saknes, augseka, augšana, AAL klasifikācija, rezistence, latvāņi, drošība).
- Mācību režīms ar pareizo atbilžu skaidrojumiem un izvēli pa tēmām.
- Atsevišķa 40 jautājumu eksāmena simulācija, jautājumi nejaušā secībā.
- Automātiska progresa saglabāšana (`localStorage`): atverot lapu atkal tajā pašā pārlūkā, mācības vai nepabeigtu eksāmenu var turpināt no iepriekšējās vietas.
- Atsevišķa poga tīšai progresa atiestatīšanai.

**Piezīme:** `scripts/merge_questions.py` pievieno jautājumus galvenajā `index.html`, nodrošina tēmu sarakstu un izvairās no identisku jautājumu dublikātiem.

## Nezāļu sakņu sistēmas

Iepriekšējā versijā papildināts ar 6 sakņu uzbūves shēmām un 36 jautājumiem, kas balstīti uz `Nezāļu klasifikācija_krāsaina.pdf`: mietsaknes, bārkšsaknes, sakneņi, sakņu dzinumi, virszemes stīgas un tīruma kosas sakneņu tīkls. [Atvērt avota PDF](https://drive.google.com/file/d/1Xs8HXCyRGYLu6-UqWV0m6V45JaAVEz2r/view).

## GitHub Pages

GitHub repozitorijā atveriet **Settings → Pages**, izvēlieties **Deploy from a branch**, `main` un `/(root)`, tad saglabājiet. Pēc publicēšanas plānotā adrese ir https://edgarsdavidsons.github.io/vaad-aal-trenazieris/ .

## Četri praktisko uzdevumu veidi

`data/advanced_questions.json` satur 76 jaunus uzdevumus: 30 smidzināšanas aprēķinus, 16 marķējuma un GHS jautājumus, 20 praktiskas situācijas, 10 vizuālas sakņu sistēmu atpazīšanas shēmas. Vizuālie attēli ir oriģinālas izglītojošas SVG ilustrācijas, nevis lauka fotogrāfijas vai oficiālu produktu etiķešu attēli. Sākotnējās nezāļu fotogrāfijas paliek galvenajā trenažierī. Visi jaunie jautājumi ir mācību materiāli, nevis oficiālie VAAD eksāmena jautājumi.
