# Équilibre — V1 application

Application mobile-first Next.js + Supabase pour menus familiaux, recettes, courses et suivi personnel.

## État de cette version

- Supabase project: configured and populated separately.
- Recipe catalog: 200 recipes across breakfast, light, vegetarian, comfort, dessert and snack categories.
- Household sharing: invite link flow is included.
- Weekly planning: breakfast daily, lunch daily, dinner daily; weekday adult lunches use the previous dinner; dinner recipes are stored at 6 servings; Friday is the free-meal slot.
- Shopping list: aggregated from recipe ingredients and household portions.
- Tracking: private weight/height/goal data per authenticated account.
- PWA manifest: included.

## Important nutrition note

The current catalog uses **editorial estimates** for kcal/serving so the application can be exercised end-to-end. They are explicitly stored as estimates in the database and should be replaced/validated against an official composition table (for example ANSES-CIQUAL) before treating the values as authoritative.

The recipe catalog is original/adapted editorial content in this project; no third-party recipe text or photographs are bulk-copied into the app.

## Environment

Create `.env.local` from `.env.example` with:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`

## Run locally

```bash
npm install
npm run dev
```

The current Supabase database is already configured for the project; the SQL files in `supabase/` are reference material for the schema/seed workflow.
