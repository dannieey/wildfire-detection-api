# PyroScope Frontend Boilerplate (DIP-12)

Vite + React starter with Mapbox GL JS installed. This is a scaffold for the interactive wildfire event prototype; the standalone HTML prototype is kept separately in `prototype/wildfire-dashboard.html`.

## Requirements
- Node.js 20+ recommended
- npm
- Optional Mapbox public access token for rendering the live basemap

## Run locally
```bash
npm install
cp .env.example .env
# Add a Mapbox public token to VITE_MAPBOX_ACCESS_TOKEN in .env (optional for build)
npm run dev
```
Open the local URL printed by Vite.

## Verify production build
```bash
npm run build
npm run preview
```

Do not commit `.env`. `VITE_*` values are exposed to the browser bundle, so only use a public Mapbox token intended for client-side use, and configure allowed URLs in Mapbox. Never put private API secrets in frontend variables.

## Current scope
This is setup boilerplate. It does not fetch NASA FIRMS observations, perform clustering, or validate wildfire incidents. Those features require later integration with the backend/data pipeline.
