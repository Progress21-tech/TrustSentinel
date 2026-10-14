# Cerviqon analyst workspace

Next.js Pages Router frontend for Cerviqon. The browser calls the configured backend directly; it contains no dashboard risk fixtures or API key.

## Configure

Copy `.env.local.example` to `.env.local` and set `NEXT_PUBLIC_API_BASE_URL` to the backend origin. Optionally set `NEXT_PUBLIC_DEMO_EMAIL` and `NEXT_PUBLIC_DEMO_PASSWORD` to prefill the login form for a dedicated, least-privilege demo account. These `NEXT_PUBLIC_` values are included in browser-delivered frontend code; never use production or privileged credentials. Prefilling does not sign the user in: clicking Continue still submits credentials to the backend's real login endpoint.

Configure backend `ANALYST_EMAIL`, `ANALYST_PASSWORD_HASH`, and `SESSION_SIGNING_SECRET` before signing in. Create the password hash from `backend/` with `python scripts/hash_analyst_password.py`; set a random session secret with at least 32 characters. Set backend `CORS_ORIGINS` to include the frontend origin.

## Develop

```powershell
npm ci
npm run dev
```

Open `http://localhost:3000`. Protected `/dashboard` routes verify the signed bearer session with `GET /v1/auth/session`. Sessions are held in browser `sessionStorage` for the current tab and expire at the backend after eight hours.

The public landing page is served at `/`. Existing analyst sign-in and dashboard routes remain at `/login` and `/dashboard`. Set `NEXT_PUBLIC_DESIGN_PARTNER_URL` to a monitored HTTPS page or `mailto:` destination before publishing the design-partner call to action. If it is unset or invalid, the page displays that the contact destination is pending; it does not claim that a form was submitted. This public value contains no secret. Privacy and legal pages also need to be published and linked before launch.

## Backend data

The overview and metrics screens read `/v1/metrics/summary`; transaction and case screens read `/v1/transactions` and `/v1/cases`; audit history uses `/v1/audit`. The scenario lab submits only the backend's supported scenario identifiers to `/v1/sandbox/scenario` and checks persisted transaction/audit records. Direct scoring uses `/v1/risk/score`. Empty and unavailable backend data are shown as such.

Synthetic scenarios create persisted synthetic records. They do not represent live payments or real-world fraud performance.

## Visual design source

The public landing page, analyst sign-in, and workspace share the Cerviqon Eucalyptus design system: Mist Green `#E9EFE7`, Soft Sage `#B8CBAE`, Dusty Clay `#D9B9A9`, and Forest Graphite `#35453B`. Shared UI colors, surfaces, borders, focus rings, and typography are defined in `styles/globals.css`; the public page's responsive layout and decorative treatments are in `styles/landing.css`. The analyst and login headers use a typographic wordmark. Space Grotesk and Inter are preferred with system fallbacks; licensed font files are not bundled, so exact font rendering depends on installed fonts.

Risk and service-status colors remain semantic so risk levels and service conditions remain distinguishable from the brand palette.
