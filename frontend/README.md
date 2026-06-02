# Frontend (Phase 6)

Minimal static chat UI with disclaimer, welcome, dynamic example chips, and chat panel.

## Local run

Serve static files from this directory:

```bash
python -m http.server 3000
```

The UI auto-calls `http://127.0.0.1:8000/api` when loaded from localhost.

## Vercel deployment

This frontend is deployment-ready for Vercel as a static site.

### Required configuration

1. Keep `frontend/vercel.json` in repo.
2. Replace this placeholder in `frontend/vercel.json`:
   - `https://REPLACE_WITH_RAILWAY_BACKEND_URL`
   - Example: `https://mfchatbot-backend-production.up.railway.app`
3. Deploy the `frontend` folder as the Vercel project root.

### How API routing works

- In production, frontend requests `/api/*`.
- Vercel rewrites `/api/*` to your Railway backend `/api/*`.
- This avoids browser CORS issues and keeps frontend code environment-agnostic.
