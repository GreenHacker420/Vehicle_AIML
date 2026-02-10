# Frontend - FleetAI Milestone-1

Next.js App Router frontend for vehicle maintenance prediction.

## Stack

- Next.js 16 (App Router)
- TypeScript
- Tailwind CSS v4
- React Query

## UI Libraries Used

- React Bits (registry components)
- Aceternity UI (registry components)
- 21st.dev (registry components)

## Start

```bash
npm install
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > .env.local
npm run dev
```

Open:

- `http://localhost:3000`
- `http://localhost:3000/predict`

## Commands

```bash
npm run lint
npm run build
```

## Main Files

- `src/app/predict/page.tsx` - prediction UX
- `src/services/predictionService.ts` - API integration layer
- `src/providers/query-provider.tsx` - React Query provider
- `src/components/ui/*` - registry-installed UI components

