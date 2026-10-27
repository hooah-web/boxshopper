# STATUS — boxshopper.dk

Sidst opdateret: 27. oktober 2026. Læs denne fil først, hvis du starter en ny session.
Historik ligger i [`docs/DAGBOG.md`](docs/DAGBOG.md), beslutninger med begrundelse i
[`docs/BESLUTNINGER.md`](docs/BESLUTNINGER.md).

## Hvad sitet er

Overblik over danske abonnementskasser. Bygget forfra efter Anders' designmockup
(`design/mockup.html`), med den viden der lå på den gamle WordPress-side ført over som
arkivtekst. Sitet er bygget og drevet af en AI, og det står i footer og på `/om/`.

## Teknisk

```
Repo        hooah-web/boxshopper
Branch      main = produktion, feat/nyt-site = PR #1
Stack       Astro 5, statisk, ingen klientframework
Byg         npx astro build           188 sider
Data        src/data/kasser.json (genereret)
Hosting     Cloudflare Pages, projekt "boxshopper-dk" (boxshopper.pages.dev var optaget)
Preview     https://feat-nyt-site.boxshopper-dk.pages.dev
```

Projektet er oprettet som Direct Upload, fordi navnet "boxshopper" var taget på
pages.dev. Det betyder, at et merge til main **ikke** udløser en deploy af sig selv:
`npx wrangler pages deploy dist --project-name=boxshopper-dk --branch=main`.
Vil vi have Git-integration i stedet, skal repoet kobles til projektet i dashboardet.

## Hvor langt er vi

- Den gamle side er kortlagt og hentet: 262 URL'er i sitemap, 243 med svar 200,
  median 209 ord pr. side. Indhold fra 2015-2021.
- 181 kasser i data. 42 med aktiv udbyder (verificeret 27.10.2026), 6 bekræftet lukkede,
  133 ikke bekræftede.
- Nyt site bygget lokalt: forside, `/boxe/` (filter + søgning), 181 kassesider,
  `/arkiv/`, `/om/`, `/kontakt/`, `/privatlivspolitik/`, 404.
- 242 redirects fra de gamle URL'er, 0 udækkede.
- Fonte selvhostet. Ingen cookies, ingen sporing, ingen annoncer.

## Næste skridt

1. Anders opretter `hooah-web/boxshopper`, så arbejdet kan pushes som PR.
2. PR med preview-deploy via Cloudflare Pages.
3. Efter godkendelse: DNS fra Simply til Cloudflare (Anders), derefter live.
4. Derefter: gennemgang af de 133 "ikke bekræftede" kasser — de skal enten bekræftes
   eller markeres lukket med belæg.

## Kendte begrænsninger

- Status "aktiv" betyder, at udbyderens forside svarede og nævnte abonnement. Det er
  ikke en garanti for, at den bestemte kasse stadig findes i samme form.
- Den gamle sides tekst er ikke omskrevet. Den vises som arkivtekst med årstal.
- `_redirects` dækker de 262 kendte URL'er. Ukendte gamle links rammer 404.
