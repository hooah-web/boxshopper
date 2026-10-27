# Beslutninger — boxshopper.dk

## 27.10.2026 — Amazon Prime får sin egen sektion

**Beslutning (Anders):** Den gamle Prime-sektion skal med, selv om den ikke er en
abonnementskasse.

**Løsning:** `/amazon-prime/` er en guide i samme design, men markeret som guide, ikke
kasse. Indholdet er skrevet forfra om det danske marked — Prime Video findes i Danmark,
det fulde Prime-medlemskab gør ikke. De 13 gamle artikler fra 2015-2017 er samlet på
`/amazon-prime/historisk/` som tydeligt markeret arkiv, fordi deres priser er i dollars
og ikke passer på Danmark i dag.

**Begrundelse:** At genudgive 2017-teksterne som fakta ville være forkert. At smide dem
væk ville tabe den viden, Anders bad om at bevare.

## 27.10.2026 — Washa er lukket

**Beslutning (Anders):** Washa flyttes til arkivet.

**Belæg:** washa.dk svarer 520, og ejeren bekræfter, at tjenesten er indstillet. Noten i
`data/curated_providers.json` vejer tungere end et domæne, der stadig svarer.

## 27.10.2026 — Pages-projektet hedder boxshopper-dk

**Beslutning:** Cloudflare Pages-projektet hedder `boxshopper-dk`, ikke `boxshopper`.

**Begrundelse:** `boxshopper.pages.dev` er optaget globalt; API'et svarede 500 på navnet
og oprettede problemfrit et projekt med et andet navn. Domænet `boxshopper.dk` er upåvirket
— det kobles på som custom domain ved go-live.

Nyeste øverst. Hver beslutning med dato, valg og begrundelse.

## 27.10.2026 — Byg forfra, og før den gamle viden med over

**Beslutning (Anders):** Sitet bygges forfra på den nye mockup. Den viden, der ligger på
den gamle WordPress-side, føres med over i stedet for at blive kasseret.

**Konsekvens:** Ny Astro-side med 181 kasser. Den gamle omtale bevares som arkivtekst med
årstal, ikke som redaktionel tekst. Gamle URL'er 301'es til de nye sider.

## 27.10.2026 — Ingen priser i v1

**Beslutning:** Sitet viser ikke priser.

**Begrundelse:** Priser på abonnementskasser ændrer sig ofte. Et pristal, der ikke er
tjekket samme dag, er en påstand vi ikke kan stå inde for. Priser, levering og
opsigelsesvilkår henvises til udbyderen.

## 27.10.2026 — Status er "udbyder aktiv", ikke "kassen findes"

**Beslutning:** Statusfeltet beskriver, om udbyderens domæne svarede og stadig beskriver
et abonnement — ikke om den bestemte kasse findes i samme form.

**Begrundelse:** Vi kan verificere et domæne og en forside. Vi kan ikke verificere et
produktsortiment uden at købe det. Sproget på siden følger, hvad der faktisk er tjekket.

## 27.10.2026 — Ingen links til genbrugte domæner

**Beslutning:** Kasser, hvis domæne i dag ejes af nogen helt andre (casino, betting,
parkeringssider), markeres lukket og får intet udgående link.

**Begrundelse:** lalatoys.dk, herrebox.dk, smartbake.dk og vegobox.com er i dag
casino-/gambling-sider. Et link ville sende læseren det forkerte sted hen og skade
troværdigheden.
