# Dagbog — boxshopper.dk

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
