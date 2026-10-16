# AI Attendance — Frontend

React 18 + TypeScript + Vite + Tailwind frontend for the AI-based Attendance
System.

It is fully decoupled from the backend: the only coupling is the base URL in
`VITE_API_URL`, so the API can be hosted anywhere.

**Backend repository:** [Mujadid2001/AI-based-Attendance-System](https://github.com/Mujadid2001/AI-based-Attendance-System)

---

## Stack

| | |
|---|---|
| Framework | React 18, TypeScript |
| Build | Vite 5 |
| Styling | Tailwind CSS 3 |
| Routing | react-router-dom 6 (`BrowserRouter`) |
| State | zustand, React Context |
| Data | axios |
| Charts | recharts |
| Camera | react-webcam |

---

## Configuration

Vite only exposes environment variables prefixed with `VITE_` to the browser.

| Variable | Purpose | Where set |
|---|---|---|
| `VITE_API_URL` | Backend API base URL, including `/api` | `.env.production` (committed) or Vercel env vars |
| `VITE_API_TIMEOUT` | axios timeout in ms | `.env.production` (committed) |
| `VITE_APP_NAME` | Shown in the UI | `.env.production` |
| `VITE_APP_VERSION` | Shown in the UI | `.env.production` |
| `VITE_DEBUG` | Debug logging | `.env.production` |

There are **no secrets** in this frontend. A Vite build inlines these values
into the JavaScript bundle, so anything placed here is public.

`.env.development` points at `http://localhost:8000/api` for local work
against a backend running on your machine.

### Changing the API URL on Vercel

Either edit `.env.production` and let Vercel rebuild on push, or set
`VITE_API_URL` in **Vercel → Settings → Environment Variables** and redeploy.
Environment variables set in the dashboard override the committed file.

---

## Local development

```bash
npm install
cp .env.development .env.local     # optional, .env.development is used as-is
npm run dev
```

Runs on <https://localhost:3000>. The dev server uses HTTPS via
`vite-plugin-mkcert`, which installs a local CA certificate so the browser
trusts the origin — needed for camera access (`getUserMedia`) on anything
other than `localhost`. That plugin requires root on your machine, which is
why it is disabled during `vite build` (see `vite.config.ts`).

If the certificate is not trusted, open the URL and accept the warning, or
run `npx mkcert -install`.

---

## Scripts

| Script | Purpose |
|---|---|
| `npm run dev` | Dev server with HTTPS on port 3000 |
| `npm run build` | Type-check (`tsc`) then build to `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | ESLint, warnings treated as errors |
| `npm run type-check` | `tsc --noEmit` |

---

## Deploying to Vercel

1. Go to <https://vercel.com/new> and import **Mujadid2001/ai-attendance-frontend**.
2. Vercel detects Vite automatically. `vercel.json` pins it anyway:
   - Framework preset: **Vite**
   - Build command: `npm run build`
   - Output directory: `dist`
   - Install command: `npm ci`
3. Deploy.

`vercel.json` also contains a rewrite so client-side routes such as
`/login` and `/students/42` serve `index.html` instead of 404-ing, which
`BrowserRouter` requires.

### After deploying, tell the backend

Vercel gives you a URL like `https://ai-attendance-frontend.vercel.app`.
Add that exact origin to the backend's `.env` on PythonAnywhere:

```
CORS_ALLOWED_ORIGINS=https://ai-attendance-frontend.vercel.app
CSRF_TRUSTED_ORIGINS=https://ai-attendance-frontend.vercel.app
FRONTEND_URL=https://ai-attendance-frontend.vercel.app
```

Then reload the PythonAnywhere web app. Without this the browser blocks every
API call with a CORS error. To use a custom domain instead, put all three
values in the custom domain's origin.

---

## Project layout

```
src/
  components/     layout, ui primitives, route guards
  config/         security configuration
  contexts/       AuthContext
  pages/          routed pages, grouped by feature
  services/       axios instance and API calls
  types/
public/           static assets copied verbatim
```

`src/services/api.ts` holds the axios instance. It attaches the JWT from
`localStorage` as `Authorization: Bearer …` and sends `withCredentials: true`
so the browser includes cookies.
