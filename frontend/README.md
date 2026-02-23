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

## Project Compatibility Check

This frontend already supports:

- `shadcn` project structure (`components.json` present)
- Tailwind CSS (`src/app/globals.css`)
- TypeScript (`tsconfig.json`)

## Default Paths

- Components: `src/components/ui`
- Styles: `src/app/globals.css`

Note:

- The requested path `/components/ui` is equivalent to `src/components/ui` in this project because the app uses a `src/` root.
- Keeping all reusable UI in `components/ui` (or `src/components/ui`) is important for consistency with shadcn conventions, easier registry installs, and predictable imports.

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
