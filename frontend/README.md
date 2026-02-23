# Frontend - FleetAI Milestone-1

Next.js App Router frontend for vehicle maintenance prediction.

## Stack

- Next.js 16 (App Router)
- TypeScript
- Tailwind CSS v4
- React Query

## UI Libraries Used

- React Bits
- Aceternity UI
- 21st.dev

## Run Locally

```bash
npm install
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > .env.local
npm run dev
```

Open:

- `http://localhost:3000`
- `http://localhost:3000/predict`

## Predict Page Output

The result screen now shows:

- risk level
- risk probability
- confidence
- row-specific meaningful insight drivers
- insight source badge (Rule Insight / GenAI Insight)
- recommendations with priority
- data quality warnings
- global feature importance table

## Deploy Frontend To Vercel

Use a separate Vercel project with root directory `frontend/`.

Required env var:

```text
NEXT_PUBLIC_API_BASE_URL=https://<backend-domain>
```

Deploy:

```bash
vercel --prod
```
