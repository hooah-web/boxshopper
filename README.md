# boxshopper.dk

Overblik over danske abonnementskasser. Astro, statisk, hostes på Cloudflare Pages.

```bash
npm install && npx astro build   # 188 sider
cd .. && python3 scripts/build_kasser.py     # data fra data/pages.json
python3 scripts/build_redirects.py           # 242 redirects
```

Læs `AGENTS.md` før du ændrer indhold. Status og næste skridt står i `STATUS.md`.
