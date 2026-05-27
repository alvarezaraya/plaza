# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

**Plaza** is a Chilean cultural events app with two independent parts:

1. **iOS app** (`Plaza/`) — SwiftUI, targets iOS 26+, uses Liquid Glass UI
2. **Python scraper** (`scraper_eventos.py`) — generates `eventos.json`, committed to `main` by GitHub Actions

The app fetches `eventos.json` from `https://alvarezaraya.github.io/plaza/eventos.json` (GitHub Pages via Fastly CDN). `docs/eventos.json` is committed alongside the root copy by CI. **Activation required once:** repo Settings → Pages → Source: `docs/` on `main`.

## Running the scraper locally

```bash
pip install requests beautifulsoup4 playwright
python -m playwright install chromium
python3 scraper_eventos.py
```

Output: `eventos.json` in the repo root (~300 events, ~9 sources). Takes 2–5 minutes.

## Building the iOS app

Open `Plaza.xcodeproj` in Xcode. Minimum deployment target is **iOS 26.0** (required for `.glassEffect()` and `Tab(role: .search)`). No SPM packages — all dependencies are system frameworks.

Liquid Glass effects only render correctly in the iOS 26 simulator or a physical device, not in SwiftUI Previews.

## Architecture

### Data flow

```
GitHub Actions (daily cron)
  → scraper_eventos.py
  → eventos.json committed to main
  → iOS app fetches via URLSession with ETag caching
  → EventoService decodes → [Evento] DTO → [Event] model
  → async: geocode venues (VenueGeocoder) + AI classify (EventClassifier)
```

### Key files

| File | Role |
|------|------|
| `EventoService.swift` | `@Observable` data service: fetches JSON, ETag caching, applies user edits, triggers geocoding + AI |
| `Models/Event.swift` | Core model + `Evento→Event` conversion, `parseName()`, `classify()`, `byComune()` filter |
| `Models/VenueGeocoder.swift` | Converts venue names to GPS coords via `MKGeocodingRequest`, caches in UserDefaults |
| `Models/EventClassifier.swift` | Apple Intelligence (`FoundationModels`) — classifies category and generates bio/preview summaries |
| `Models/ComunaManager.swift` | Manages selected location filter; `"Chile"` means show all |
| `Theme/PlazaTheme.swift` | All design tokens: colors (`plFg`, `plAccent`, `plBg`…), fonts (`plDisplay`, `plSans`, `plMono`), spacing (`PlSpace`), `PlTag` component |
| `App/RootTabView.swift` | iPhone tab bar + iPad sidebar layout (375pt floating panel over full-screen map) |
| `scraper_eventos.py` | Multi-source scraper; Playwright for JS-rendered sites (ComediaTicket); RSS for WordPress sites (CulturaAntofagasta, CulturaIquique) |

### UserDefaults keys

| Key | Content |
|-----|---------|
| `plaza_edited_events` | `[String: EditedFields]` — user-edited event fields |
| `plaza_saved_events` | `[String]` — saved event stableIDs |
| `plaza_etag` | ETag for conditional fetch of eventos.json |
| `plaza_cached_json` | Last fetched eventos.json bytes (offline fallback) |
| `plaza_geocode_cache` | `[String: CachedCoordinate]` — geocoded venue coordinates |
| `plaza_theme` | `"plaza"` or `"multicolor"` |
| `plaza_onboarding_done` | Bool — onboarding gate |

### Event identity

Events are grouped by `groupKey` (lowercased title). Multiple dates for the same event are collapsed into a single `Event` with `otherDates: [DateEntry]`. The `stableID` is the source URL — used to persist edits and saves across JSON refreshes.

### Enriquecimiento paralelo

`enriquecer_evento()` (Wikipedia + DuckDuckGo) corre con `ThreadPoolExecutor(max_workers=6)` en `main()`. Las llamadas de red a Wikipedia/DDG están protegidas por `_enrich_lock = threading.Semaphore(1)` para no saturar las APIs públicas — solo un worker hace requests de enriquecimiento a la vez. La lista `todos` se escribe de vuelta en orden una vez que cada `Future` completa.

### Coordenadas en JSON

`eventos.json` incluye `lat` y `lon` para cada evento (generados por `geocodificar_todos()` en el scraper). El scraper primero consulta `COORDENADAS_FIJAS` (dict hardcoded de venues/ciudades conocidas), luego Nominatim (OpenStreetMap, ToS: 1 req/s). En la app, `Event.from()` usa estas coordenadas directamente; `geocodeEvents()` solo llama a `VenueGeocoder` como fallback para eventos que lleguen sin coordenadas (aún en `Event.defaultCoordinate`).

### Scraper sources

| Source | Method | Notes |
|--------|--------|-------|
| Ticketplus.cl | `requests` + BS4 | All 16 regions, cap 40 events/region |
| Ticketpro.cl | `requests` + BS4 | No city filter |
| PuntoTicket.com | `requests` + BS4 | `/todos` + `/evento/` paths |
| Ticketmaster.cl | `requests` + BS4 | Scrapes home (search is anti-bot) |
| Passline.com | Playwright | Home only — city URLs return 403 |
| ComediaTicket.cl | Playwright | JS-rendered SPA React |
| EsquinaRetornable.cl | `requests` + BS4 | WordPress, cine arte Antofagasta |
| CulturaAntofagasta.cl | RSS (`/feed/`) | WordPress RSS |
| CulturaIquique.cl | RSS (`/feed/`) | WordPress RSS |
| Ticketchile.cl | `requests` + BS4 | `/evento/` URLs, ciudades medianas |
| MasQueTickets.cl | `requests` + BS4 | Teatro y artes escénicas |
| Eventbrite.cl | Playwright | `/d/chile/events/` — SPA React |
| Joinnus.com/CL | Playwright | URL pattern `/CL/[cat]/[slug]-[id]` |
| RSS Municipales | RSS (`/feed/`) | CulturaGob, CCPLM, GAM, CulturaValparaíso |

### CI

`.github/workflows/scraper.yml` runs at 06:00 UTC and 17:00 UTC. Chromium is cached with `actions/cache@v4` (key includes OS + requirements hash); on cache hit only `install-deps` runs (~10s vs ~2 min). Commits `eventos.json` to `main` after each run.

## Design tokens

Theme colors are accessed as `Color.plBg`, `Color.plAccent`, etc. — computed properties that read the active `AppTheme` from UserDefaults at call time. Theme changes are applied by reinitializing the `WindowGroup` with `.id(themeRaw)`.

Fonts: use `Font.plDisplay()` for titles, `Font.plSans()` for UI text, `Font.plMono()` for tags/coordinates. `InstrumentSerif` and `JetBrainsMono` TTFs are bundled but `plSerifItalic` and `plMono` fall back to system serif/monospaced.

The `isIPadSidebar` environment key is set to `true` for all views rendered inside the iPad floating panel; use it to switch backgrounds from opaque to `.clear`.
