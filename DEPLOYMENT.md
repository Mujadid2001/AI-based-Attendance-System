# Deploying the backend to PythonAnywhere

Target: a Django + DRF API on a PythonAnywhere web app, backed by a SQLite
file inside the project folder and served over HTTPS through PythonAnywhere's
proxy.

---

## 1. What you need first

| Thing | Where to get it |
|---|---|
| A PythonAnywhere account with a web app | pythonanywhere.com |
| A deployed React frontend (for CORS) | wherever you host the frontend |
| A Google App Password (for email) | myaccount.google.com/apppasswords |
| (optional) A custom domain + HTTPS | PythonAnywhere **Web** tab |

A database is **not** required - the app ships configured for SQLite inside the
project folder. See section 5.

---

## 2. Get the code onto the server

```bash
git clone <your-repo-url> ~/AI-based-Attendance-System
cd ~/AI-based-Attendance-System
```

The project must live under `/home/mujadid/`, otherwise PythonAnywhere
cannot serve static files or media from it.

---

## 3. Create a virtualenv

PythonAnywhere ships its own venv per account, but a project-local one is
cleaner:

**Bash console:**

```bash
cd ~/AI-based-Attendance-System
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Only install `requirements.txt`. The heavy machine-learning libraries in
`requirements-optional.txt` (dlib, face-recognition, OpenCV) need a compiler
and long build times; the app runs without them (see section 9).

---

## 4. Configure the environment

```bash
cp .env.production .env
nano .env
```

Replace every line marked `>>> CHANGE_ME`. The full annotated version of the
same file lives in the repo root as `.env`, so you can diff the two and see
exactly which values differ.

The critical ones:

As shipped, `.env.production` is **already correct** except for two lines:

| Line | Why you must change it |
|---|---|
| `EMAIL_HOST_PASSWORD` | your 16-character Google App Password |
| `CORS_ALLOWED_ORIGINS` / `CSRF_TRUSTED_ORIGINS` / `FRONTEND_URL` | the deployed React origin - currently `http://localhost:3000` because the frontend is not deployed yet |

Everything else already matches this project: `ALLOWED_HOSTS` and
`SERVER_BASE_URL` are `mujadid.pythonanywhere.com`, the database is SQLite,
`SECRET_KEY` and `ENCRYPTION_KEY` are set.

To see what is still outstanding:

```bash
grep '>>> CHANGE_ME' .env
```

To inspect the environment the way Django will read it:

```bash
set -a; . ./.env; set +a
python attendance_system/manage.py check --deploy
```

> The secrets in `.env.production` are committed on purpose, so the local
> `.env` and production share one value. That means anyone with repo access
> can forge session cookies and read encrypted columns. Rotate both with:
> ```bash
> python -c "import secrets,string;a=string.ascii_letters+string.digits+'-_=+.';print(''.join(secrets.choice(a) for _ in range(64)))"
> python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
> ```
> (`get_random_secret_key()` is avoided here because it can emit `)` and `^`,
> which break `sh`. Rotating `ENCRYPTION_KEY` makes existing encrypted rows
> unreadable.)

The app refuses to start if `SECRET_KEY` is too short, if `ENCRYPTION_KEY` is
not a valid Fernet key, if `CORS_ALLOWED_ORIGINS` is empty, or if
`CORS_ALLOW_ALL_ORIGINS` is `True`. That is deliberate: each of those is a
silent, hard-to-diagnose failure later.

---

## 5. Create the database

The app uses **SQLite**, and the file lives inside the project:

```
/home/mujadid/AI-based-Attendance-System/attendance_system/db.sqlite3
```

That location matters: PythonAnywhere cannot read or write outside
`/home/mujadid/`. It is git-ignored, so each machine gets its own.

```bash
source .venv/bin/activate
cd ~/AI-based-Attendance-System
python attendance_system/manage.py migrate
python attendance_system/manage.py collectstatic --noinput
python attendance_system/manage.py createsuperuser
```

`collectstatic` is **required** for hashed filenames and long-lived cache
headers. If you skip it the site still works, just unhashed - the settings
detect the missing manifest and fall back automatically rather than erroring.

### SQLite's one real limitation

SQLite locks the **entire database** for the duration of every write. With a
single user, or one web worker, you will never notice. The moment two people
mark attendance at the same time, writes queue behind each other. Two
mitigations are already in place (`timeout: 20` so requests wait instead of
failing instantly, and no persistent connections so a write lock is never
held open).

When that becomes a problem, switch to the MySQL that comes free with
PythonAnywhere - **Databases** tab -> create -> paste five values:

```
DB_ENGINE=django.db.backends.mysql
DB_NAME=mujadid$attendance_db
DB_USER=mujadid
DB_PASSWORD=<from the Databases tab>
DB_HOST=mujadid.mysql.pythonanywhere-services.com
DB_PORT=3306
```

then `migrate` again. No code changes are needed.

---

## 6. Point the WSGI file at the project

**Web tab -> WSGI configuration file**, replace the entire contents with:

```python
import sys
sys.path.insert(0, '/home/mujadid/AI-based-Attendance-System')

from pythonanywhere_wsgi import application
```

**Web tab -> Environment variables**, add only if you want to override what
`.env` already says:

```
DJANGO_SETTINGS_MODULE=config.settings.production
```

Everything else belongs in `.env`, not in the Web tab, so it is versioned
alongside the rest of the configuration.

---

## 7. Map static files (and media)

**Web tab -> Static files**, add two entries:

| URL | Directory |
|---|---|
| `/static/` | `/home/mujadid/AI-based-Attendance-System/attendance_system/staticfiles` |
| `/media/` | `/home/mujadid/AI-based-Attendance-System/attendance_system/media` |

`/static/` is also served by WhiteNoise as a fallback, so the admin looks
right even if you forget this step. `/media/` has no fallback: either map it,
or leave `SERVE_MEDIA_FILES=True` in `.env` and let Django serve it (slower,
but nothing 404s).

Then hit the big green **Reload** button.

---

## 8. Verify

```bash
curl -i https://<username>.pythonanywhere.com/api/health/
```

```json
{"status": "healthy", "service": "AI Attendance System API", "database": "ok"}
```

Also check, in a browser:

- `https://mujadid.pythonanywhere.com/admin/` - log in, styled correctly
- `https://mujadid.pythonanywhere.com/api/` - endpoint index

### If you get an infinite redirect loop

`SECURE_SSL_REDIRECT` is the usual cause. PythonAnywhere terminates TLS and
forwards the original scheme in `X-Forwarded-Proto`; the app reads that
header via `SECURE_PROXY_SSL_HEADER` in `config/settings/base.py`. If you have
edited that away, put it back, or set `SECURE_SSL_REDIRECT=False` in `.env` as
a stopgap.

### If you get `no such table`

`migrate` did not run, or `DB_NAME` points somewhere else. With SQLite, run
`ls -la attendance_system/db.sqlite3` - the file should exist.

### If the admin returns 403 "Request blocked due to security policy"

`BLOCK_SUSPICIOUS_REQUESTS=True` should no longer block `/admin/`; that was a
bug where the admin path was listed as an attack pattern. If you see this,
check that `apps/enterprise_security/middleware.py` no longer contains
`'admin/'` in `suspicious_patterns`.

### If password reset says "email sent" but nothing arrives

Three things are required, in order: `EMAIL_BACKEND` must be the SMTP backend,
`EMAIL_HOST_PASSWORD` must be a real App Password (not your account
password), and the account must have 2-Step Verification enabled. Emails are
only printed to the log with the console backend.

---

## 9. What is degraded on PythonAnywhere, and why

PythonAnywhere gives you one web process and a MySQL server. No Redis, no
Celery worker, no cron. Each of those has a configured fallback so nothing
breaks:

| Feature | Without the external service | Controlled by |
|---|---|---|
| Redis cache | in-process `LocMemCache` | `USE_REDIS=False` |
| WebSockets | in-process channel layer | `USE_REDIS=False` |
| Celery tasks | run inline in the request | `CELERY_TASK_ALWAYS_EAGER=True` |
| Facial recognition | endpoints return `503` | install `requirements-optional.txt` |
| `psutil` metrics | `/api/security/health/` omits them | install `psutil` |

`task.delay()` still works with eager mode - the task just runs before the
response returns. Report generation and reminder emails keep working; they
are simply not backgrounded.

Ask the frontend to call `GET /api/ai/configuration/status/` on startup. It
always returns 200 and tells the UI which AI features to show:

```json
{
  "facial_recognition": {"available": false, "reason": "...", "threshold": null},
  "voice_notifications": {"available": false}
}
```

---

## 10. Turning on HSTS (do this last)

Once the domain has been HTTPS-only for a while, and you are sure nothing
serves it over plain http:

```
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

Browsers cache HSTS aggressively and it is effectively irreversible per
domain. Start at `0`, which is the default.

---

## 11. Updating later

```bash
source .venv/bin/activate
cd ~/AI-based-Attendance-System
git pull
pip install -r requirements.txt
python attendance_system/manage.py migrate
python attendance_system/manage.py collectstatic --noinput
```

Then reload from the Web tab. `.env` is git-ignored, so a pull never
overwrites your secrets.

---

## 12. The frontend is a separate repository

The React app is **not** in this repository. It lives at:

    https://github.com/Mujadid2001/ai-attendance-frontend

Deploy it to Vercel independently of the API — pushing to one repo does not
rebuild the other. The only contract between them is `VITE_API_URL`.

### After the frontend is live

Vercel assigns an origin such as `https://ai-attendance-frontend.vercel.app`.
Put that **exact** origin into `.env` on the PythonAnywhere server:

```
CORS_ALLOWED_ORIGINS=https://ai-attendance-frontend.vercel.app
CSRF_TRUSTED_ORIGINS=https://ai-attendance-frontend.vercel.app
FRONTEND_URL=https://ai-attendance-frontend.vercel.app
```

Then reload the web app. Skip this and the browser blocks every API call with
a CORS error, and password-reset emails link back to `localhost:3000`.

### Working on both locally

```bash
git clone git@github.com:Mujadid2001/AI-based-Attendance-System.git
git clone git@github.com/Mujadid2001/ai-attendance-frontend.git
```

Run the API on `:8000` and the frontend on `:3000`; the frontend's
`.env.development` already points at `http://localhost:8000/api`.

---

## 13. Local development

```bash
cd AI-based-Attendance-System
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python attendance_system/manage.py migrate
python attendance_system/manage.py runserver
```

`.env` in the repo root is pre-filled with working local values (SQLite,
console email, `DEBUG=True`) and documents every setting name. Leave
`SERVER_BASE_URL` empty so the app detects your LAN IP and phones on the same
Wi-Fi can reach the dev server.

Optional, only if you have a compiler and want face recognition locally:

```bash
sudo apt-get install -y cmake build-essential libboost-all-dev \
    libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev espeak1
pip install -r requirements-optional.txt
```
