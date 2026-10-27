# Dagbog — boxshopper.dk

## 27. oktober 2026 (sen aften)

- Anders: fjern kildeangivelser, og brug en skarp regel for aktive kasser — kun hvis
  udbyderens side selv skriver at man kan købe en kasse, med pris.
- Gennemgik alle 40 aktive med tre metoder (rå HTML, målrettede abonnementsstier og
  vurdering af uddrag). 33 flyttet til arkivet, 7 står tilbage.
- Kendte sager: Sundtakeaway fører nu til BetterFeast, Nordic Hiit sælger online træning,
  Luxplus og Plusbog sælger medlemskaber, Birchbox og Dollar Shave Club er udenlandske.
- Kreakassen og Noru lukket efter besked fra Anders.
- Forsiden viser nu kun kategorier med mindst én aktiv kasse.

## 27. oktober 2026 (aften)

- Washa flyttet til arkivet efter besked fra Anders: washa.dk svarer 520. Noter i
  `curated_providers.json` vejer nu tungere end et domæne, der stadig svarer.
- Amazon Prime-sektion bygget: hub + fire guidesider + historisk side med 2017-teksterne.
  Indholdet er skrevet forfra ud fra Amazon og madskristensen.dk, fordi de gamle tekster
  beskriver det amerikanske Prime med dollarpriser.
- De 13 gamle Prime-URL'er 301'es ind i guiden. 254 redirects i alt, 0 udækkede.
- Guide-strimlen på forsiden flyttet ned under "Sådan finder du en kasse", så den ikke
  står som to mørke blokke efter hinanden. Kortuddrag klippes nu ved sætningsslut.

## 27. oktober 2026 (senere)

- Anders sendte WordPress-eksporten (`WordPress.2026-10-27.xml`): 231 offentliggjorte
  indlæg/sider, 310 vedhæftede filer, 31 tags, 40 kategorier, 587 kommentarer.
- Hentede 309 mediefiler gennem Chrome (WAF'en blokerer curl). To filer var en mp3 og en
  pdf. 175 kasser har fået et logo, konverteret til WebP (9 KB pr. billede).
- Tags fra eksporten er lagt på kasserne og bruges som filter. 34 af 42 aktive kasser
  har mindst ét tag.
- Eksporten indeholder kommentarer med personoplysninger. Den rå XML er slettet igen;
  kun `data/wxr.json` uden kommentarer er bevaret.

## 27. oktober 2026

- Kortlagde den gamle side: WordPress + Yoast på Simply.com shared hosting, DNS hos
  Simply, ingen Cloudflare-zone. Sitemap havde 262 URL'er (204 indlæg, 29 sider,
  30 kategorier, 28 tags).
- Sitet er teknisk i stykker: PHP-warnings printes ind i brødteksten med serverstier
  (`/var/www/opskriftpandekager.dk/boxshopper.dk/...`), annoncekoden vises som tekst, og
  temaets overskrift er "Mindblown: a blog about philosophy.".
- Search Console: property findes kun som `http://boxshopper.dk/`, sitemaps indsendt i
  2017. 12 måneder: 6 klik, 302 visninger.
- Hentede alle 262 sider som HTML via lokal Chrome (WAF'en svarer 454 til curl).
  Udtræk til `data/pages.json`: median 209 ord pr. side, indhold 2015-2021.
- Tjekkede udbyderdomæner i tre runder. 42 kasser har en aktiv udbyder. Seks domæner
  er i dag casino/betting-sider (lalatoys.dk, herrebox.dk, smartbake.dk, vegobox.com) —
  de markeres lukket og linkes der ikke til.
- Anders leverede designmockup (`design/mockup.html`). Sitet er bygget i Astro efter
  mockuppen, med rigtige sider i stedet for SPA-visninger.
- 242 redirects genereret, 0 gamle URL'er uden destination. Build: 188 sider.
