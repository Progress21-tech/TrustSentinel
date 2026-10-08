# TrustSentinel analyst workspace

Next.js Pages Router frontend for TrustSentinel. The browser calls the configured backend directly; it contains no dashboard risk fixtures or API key.

## Configure

Copy `.env.local.example` to `.env.local` and set `NEXT_PUBLIC_API_BASE_URL` to the backend origin. Optionally set `NEXT_PUBLIC_DEMO_EMAIL` and `NEXT_PUBLIC_DEMO_PASSWORD` to prefill the login form for a dedicated, least-privilege demo account. These `NEXT_PUBLIC_` values are included in browser-delivered frontend code; never use production or privileged credentials. Prefilling does not sign the user in: clicking Continue still submits credentials to the backend's real login endpoint.

Configure backend `ANALYST_EMAIL`, `ANALYST_PASSWORD_HASH`, and `SESSION_SIGNING_SECRET` before signing in. Create the password hash from `backend/` with `python scripts/hash_analyst_password.py`; set a random session secret with at least 32 characters. Set backend `CORS_ORIGINS` to include the frontend origin.

## Develop

```powershell
npm ci
npm run dev
```

Open `http://localhost:3000`. Protected `/dashboard` routes verify the signed bearer session with `GET /v1/auth/session`. Sessions are held in browser `sessionStorage` for the current tab and expire at the backend after eight hours.

## Backend data

The overview and metrics screens read `/v1/metrics/summary`; transaction and case screens read `/v1/transactions` and `/v1/cases`; audit history uses `/v1/audit`. The scenario lab submits only the backend's supported scenario identifiers to `/v1/sandbox/scenario` and checks persisted transaction/audit records. Direct scoring uses `/v1/risk/score`. Empty and unavailable backend data are shown as such.

Synthetic scenarios create persisted synthetic records. They do not represent live payments or real-world fraud performance.

## Visual design source

The TrustSentinel visual tokens are based on the supplied pitch deck's embedded RGB vector colors: `#F2F7FA` background, `#164B82` brand blue, `#343434` text, `#C8D1D9` dividers, plus white and black. `#E7EFF6` is a light brand-blue tint for interactive surfaces. Risk and service-status colors remain semantic. The deck embeds Telegraf (UltraLight, Regular, Bold), TT Hoves Regular, and Noto Sans Bold. Those licensed font files are not included in the frontend, so the CSS names them first and falls back to installed system sans-serif fonts; exact font rendering requires appropriately licensed font files.
