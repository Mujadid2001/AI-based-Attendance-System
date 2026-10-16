# AI-based Attendance System — Backend

Django 4.2 + Django REST Framework API for the AI-based Attendance System.

**This repository is the backend only.** The React frontend lives in its own
repository:

| | |
|---|---|
| Backend (this repo) | https://github.com/Mujadid2001/AI-based-Attendance-System |
| Frontend | https://github.com/Mujadid2001/ai-attendance-frontend |
| Deployed API | `https://mujadid.pythonanywhere.com/api` |
| Deployed frontend | Vercel (see the frontend README) |

The two are fully decoupled: the frontend only needs the API base URL, set
through `VITE_API_URL`. Nothing in the frontend imports anything from here.

---

## Working on the full stack

```bash
git clone git@github.com:Mujadid2001/AI-based-Attendance-System.git
git clone git@github.com/Mujadid2001/ai-attendance-frontend.git
```

Run the API on `:8000` and the frontend on `:3000`. The frontend's
`.env.development` already points at `http://localhost:8000/api`.

---

## Requirements

- Python 3.11+
- Node 18+ (only for the frontend)

Install:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` holds only packages that install cleanly on PythonAnywhere.
The heavy machine-learning libraries (`dlib`, `face-recognition`, OpenCV,
`librosa`) are optional and live in `requirements-optional.txt` — see
[Facial recognition](#facial-recognition).

---

## Quick start

```bash
cp .env .env.local          # optional; .env already works as-is
python attendance_system/manage.py migrate
python attendance_system/manage.py createsuperuser
python attendance_system/manage.py runserver
```

Configuration is entirely environment-driven from `.env` in the repository
root. `.env.production` is the matching deployment template: identical setting
names, so values copy across directly.

```bash
grep '>>> CHANGE_ME' .env.production     # what still needs filling in
```

---

## Layout

```
attendance_system/
  config/settings/     base / development / production
  apps/
    authentication/    users, JWT login, password reset, email verification
    student/           students, courses, enrollments, face images
    attendance/        sessions, records, reports
    ai_core/           facial recognition pipeline, face registration
    camera_integration/  camera sources, streaming, QR codes
    enterprise_security/  audit log, 2FA, encryption, compliance
  utils/               base viewsets, response helpers, network detection
models/                dlib 68-point landmark predictor, face encodings
DEPLOYMENT.md          step-by-step PythonAnywhere deployment
```

---

## Authentication

JWT, obtained from `POST /api/token/` with `email` and `password`:

```bash
curl -X POST https://mujadid.pythonanywhere.com/api/token/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"..."}'
```

Send the access token as `Authorization: Bearer <token>`. Refresh tokens
rotate on use and the previous one is blacklisted, so a refresh token can only
be redeemed once.

Roles are `admin`, `teacher` and `student`. The Django admin at `/admin/` is
for staff use only.

---

## Facial recognition

`dlib`, `face-recognition` and OpenCV are **optional**. Without them the app
boots normally and the affected endpoints return `503` with a clear message
instead of crashing. Ask the frontend what is available:

```bash
curl -H "Authorization: Bearer $TOKEN" https://mujadid.pythonanywhere.com/api/ai/configuration/status/
```

```json
{
  "facial_recognition": {"available": false, "reason": "...", "threshold": null},
  "voice_notifications": {"available": false}
}
```

To enable it on a machine with a compiler:

```bash
sudo apt-get install -y cmake build-essential libboost-all-dev \
    libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev espeak1
pip install -r requirements-optional.txt
```

PythonAnywhere's shared and free tiers cannot install these, so expect
`available: false` there.

---

## Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** — PythonAnywhere + SQLite, HTTPS,
static and media mapping, and the `.env` values to fill in.

The app targets a single web process with no Redis, no Celery worker and no
reverse proxy. Each of those is optional and degrades to an in-process
fallback, so nothing external needs to be provisioned.

---

## Tests

The CI workflow (`.github/workflows/django.yml`) runs `check`,
`check --deploy` against production settings, `makemigrations --check`,
`migrate`, `collectstatic`, and an endpoint smoke test.

```bash
python attendance_system/manage.py check
python attendance_system/manage.py check --deploy      # with production settings
python attendance_system/manage.py makemigrations --check --dry-run
python attendance_system/manage.py test
```

There is no unit test suite yet, so `manage.py test` passes trivially. The
smoke test in CI is what currently guards against regressions.
