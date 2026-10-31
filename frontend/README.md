# OpenPK-Twin Web

React + Vite frontend for the OpenPK-Twin pharmacokinetic simulation API.

## Features

- One-compartment IV bolus population simulation
- Two-compartment IV bolus population simulation
- Configurable virtual-patient count, duration, sampling points and random seed
- Configurable inter-individual CV values
- Median and 5th–95th percentile concentration-time visualisation
- Representative virtual-patient curves
- CSV export of returned population summaries and representative profiles
- API health indicator and validation/error messages

## Requirements

- Node.js 20.19+ or 22.12+
- npm

## Run locally

```bash
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:5173.

By default, the app calls the public API at `https://openpk-twin-api.onrender.com`. The FastAPI CORS configuration must allow `http://localhost:5173` for local browser access.

## Production build

```bash
npm run build
npm run preview
```

Vite writes the production site to `dist/`.

## Deploy to Vercel from this monorepo

1. Import `CodebreakerComeback/openpk-twin` into Vercel.
2. Set **Root Directory** to `frontend`.
3. Use the Vite framework preset (or build command `npm run build` and output directory `dist`).
4. Add environment variable `VITE_API_BASE_URL` with value `https://openpk-twin-api.onrender.com` for Production, Preview and Development as appropriate.
5. Deploy.
6. Copy the resulting production origin (for example `https://your-project.vercel.app`).
7. In Render, open the `openpk-twin-api` service → Environment and set `OPENPK_CORS_ORIGINS` to the exact Vercel origin. For local development, include both origins separated by a comma:

   `https://your-project.vercel.app,http://localhost:5173`

8. Save/redeploy the Render service and test both simulation endpoints from the website.

## Scientific-use notice

OpenPK-Twin Web is for education and research. The current population engines use simplified model assumptions and independently sampled lognormal variability. Outputs are simulated, are not patient-specific predictions, and must not be used for clinical dosing or medical decisions.
