# AGENTS.md — boxshopper.dk

Læs denne fil, før du ændrer noget på sitet.

## Hvad sitet er

Overblik over danske abonnementskasser: hvad de indeholder, hvem de passer til, og om
udbyderen stadig er aktiv. Sitet er **ikke** en anmeldelse — ingen på siden har prøvet
kasserne, og der skrives ingen erfaringer, smagsdomme eller testresultater.

Sitet er bygget og drevet af en AI for Hooah. Det står i footeren og på `/om/`.

Konkurrenter: `abonnement.dk`, `subhub.dk`, `boxdeal.dk`. Vi slår dem på at vise status
og kilde i stedet for at påstå mest muligt.

## Målgruppe og tone

Danskere der overvejer en abonnementskasse og vil vide, om den stadig findes, før de
bruger tid på den. Kort, konkret dansk. Ingen adjektiver, ingen "fantastisk", ingen
sælgende sprog. Skriv hvad kilden viser, og hvornår den er tjekket.

## Teknisk

```
Stack       Astro 5, statisk, ingen klientframework (kun små inline-scripts)
Hosting     Cloudflare Pages, projekt "boxshopper"
Byg         npx astro build          (188 sider)
Data        src/data/kasser.json  (genereret — rediger ikke i hånden)
```

Sider: `/`, `/boxe/`, `/box/<slug>/`, `/arkiv/`, `/om/`, `/kontakt/`,
`/privatlivspolitik/`, 404.

`public/_redirects` genereres af `scripts/build_redirects.py` ud fra den gamle
WordPress-sides 262 URL'er. Kør scriptet igen, hvis URL-listen ændrer sig.

Fonte ligger lokalt i `public/fonts/` med `@font-face` i
`src/styles/fonts.css`. Der indlæses intet fra Google.

## Data — kilder er sandhed

`kasser.json` bygges af `scripts/build_kasser.py` ud fra:

```
data/pages.json             262 sider hentet fra den gamle WordPress-side
data/curated_providers.json håndverificerede udbydere (domæne + kategori)
data/subscription_check.json belæg: svarer domænet, og nævner forsiden abonnement
```

Status er **ikke** en vurdering:

- `active` — udbyderens domæne svarede 200 ved tjek, og forsiden nævnte mindst to
  abonnementsord. Betyder "udbyderen er aktiv", ikke "kassen findes i denne form".
- `closed` — domænet er væk, parkeret eller solgt til noget helt andet (flere er i dag
  casino-sider). Noten i `curated_providers.json` skal sige hvad der blev set.
- `unknown` — alt andet. Vi skriver aldrig "lukket", fordi et domæne ikke svarede.

Ingen priser på sitet. Priser ændrer sig, og et tal uden samme-dags-tjek er en påstand.

## Regler der ikke må brydes

1. Link aldrig til et domæne, der ikke er verificeret som udbyderens eget. Flere gamle
   domæner (lalatoys.dk, herrebox.dk, smartbake.dk) er i dag casino-sider.
2. Den gamle omtale gengives som arkivtekst med årstal. Den må ikke pyntes eller
   blandes med nye påstande.
3. Ingen annoncer, affiliate-links eller sporing i v1. Kommer det, skal
   `/privatlivspolitik/` opdateres i samme ændring.
4. AI-åbenhed: footeren og `/om/` skal blive stående.
