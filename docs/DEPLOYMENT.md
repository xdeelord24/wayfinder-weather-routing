# Deployment and submission

**Hosted application:** [https://xdeelord.pythonanywhere.com](https://xdeelord.pythonanywhere.com).

Wayfinder was deployed on October 26, 2026 using PythonAnywhere, Python 3.12, and one WSGI worker. The public health endpoint, live routing/weather, frontend assets, and demo HTTP scenarios passed verification. A map-tile referrer-policy issue found during browser checking was corrected and verified on the host: real tiles, routes, heatmap, checkpoint details, and the +0/+24/+48-hour controls rendered correctly in the desktop demonstration. Mobile verification is still the historical local check. The Loom recording is pending. See [VERIFICATION.md](VERIFICATION.md) for the evidence and scope.

The free web app currently expires on **November 26, 2026** and requires manual monthly renewal from the account. Keep the site renewed while it is under review.

## PythonAnywhere deployment

The deployed project is `/home/xdeelord/wayfinder`. Initial bundle `wayfinder-pythonanywhere-20261026T004930Z.zip` contained the runtime from revision `20b2528`, built frontend, requirements, and WSGI template. It has 22 files and expands to about 2.31 MB; credentials, the assessment PDF, tests, virtualenvs, and local evidence are excluded. The deployed settings now include `SECURE_REFERRER_POLICY="strict-origin-when-cross-origin"` so cross-origin OpenStreetMap tile requests retain an origin referrer. Local and hosted settings hashes match. Regenerate the bundle before another deployment to include that correction.

Disk use after installation was approximately **218 MiB according to `du`**, while the dashboard reported about **230 MB of its 512 MB quota**. These are deployment-time observations. Avoid pip caches and duplicate environments.

To reproduce the setup:

1. Build the frontend locally, then run `python scripts/package_deployment.py`. Inspect the generated ZIP and manifest under `output/deployment/` before upload. The script checks ZIP integrity, allowed paths, and hashes; it neither includes secrets nor deploys the app.
2. Extract the ZIP under `/home/YOUR_USERNAME`, producing `/home/YOUR_USERNAME/wayfinder`.
3. Create an isolated environment with `python3.12 -m venv /home/YOUR_USERNAME/wayfinder/.venv`, then run `/home/YOUR_USERNAME/wayfinder/.venv/bin/pip install --no-cache-dir --only-binary=:all: -r /home/YOUR_USERNAME/wayfinder/requirements.txt`. The installed native dependencies have compatible Linux wheels; the optional Numba extra is unnecessary.
4. Add a web app using **Manual configuration**, matching its Python version to the virtualenv. Set its virtualenv path to `/home/YOUR_USERNAME/wayfinder/.venv`, source code to `/home/YOUR_USERNAME/wayfinder/backend`, and working directory to `/home/YOUR_USERNAME/wayfinder`. Enable Force HTTPS. PythonAnywhere supplies WSGI; do not start Gunicorn or `runserver` there.
5. Copy `pythonanywhere_wsgi.py.example` into the WSGI file linked from the Web tab. Replace `YOUR_USERNAME`, add the project's `backend` directory to `sys.path`, and use `config.settings`. This platform file is separate from the repository's `backend/config/wsgi.py`.
6. Create a private project-root `.env` with a new strong `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, the exact public hostname in `DJANGO_ALLOWED_HOSTS`, and the server-only `TOMTOM_API_KEY`. Set permissions to `600`. The deployed hostname is `xdeelord.pythonanywhere.com`; `manage.py check` passed with production settings.
7. Reload, then run the public verification commands below. WhiteNoise serves `frontend/dist`, including `/assets`; this bundle needs no host-side Node build, database migrations, or duplicate static collection.

TomTom and Open-Meteo were successfully reached from this deployment. HTTPX uses the host's proxy environment by default. Official references: [Django deployment](https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/) and [virtualenv configuration](https://help.pythonanywhere.com/pages/VirtualEnvForNewerDjango/).

## Verify the public deployment

Run locally; these commands use public endpoints without deployment credentials:

```powershell
.\.venv\Scripts\python.exe scripts/verify_hosted.py https://xdeelord.pythonanywhere.com
.\.venv\Scripts\python.exe scripts/smoke.py https://xdeelord.pythonanywhere.com --frontend
```

The live verifier makes at most six requests, without retries: health, frontend HTML, two live location searches, one live plan, and its corridor. It checks server-selected IDs, arrival-time forecasts, mileage conservation, all 49 frames, and the 200-cell bound. A provider returning fewer than three alternatives is recorded as a shortfall. Evidence is written under `output/live-verification/`.

The separate demo smoke verifies frontend assets and the mixed, clear, and blocked scenarios. Visible checks must also cover map tiles, route/checkpoint selection, slider, mobile layout, reload, and attribution. HTTP results alone do not certify rendering or every interaction.

## Optional Docker hosts

The Dockerfile, `railway.json`, and `render.yaml` remain available for alternate hosts; they are not the active deployment. Docker builds the frontend and runs Gunicorn with one worker, using the host's `PORT` and `/api/health`. Configure the actual hostname and server secrets separately. Railway also needs `healthcheck.railway.app` in `DJANGO_ALLOWED_HOSTS`; see its [health-check documentation](https://docs.railway.com/deployments/healthchecks). Verify a replacement host before changing the submission URL.

## Runtime configuration

Use `.env.example` as the authoritative list of supported names. The TomTom key must be available only to the backend. Do not place it in a frontend `VITE_` environment variable, source code, screenshots, or submission text.

The optional Docker command runs Gunicorn with one worker and eight threads; PythonAnywhere instead supplies its WSGI worker. Keep one worker while using the local-memory plan cache: multiple worker processes would not share plan IDs. Plans expire after one hour or disappear when the process restarts; an unavailable plan requires a new planning request. A multiworker deployment should first move this cache and throttling state to a shared service.

For an optional local container check, use Docker Desktop in Linux-container mode:

```powershell
docker build -t wayfinder .
docker run --rm -p 8000:8000 --env-file .env wayfinder
```

Open `http://localhost:8000` and `http://localhost:8000/api/health`. These commands validate the container locally; each public host must be checked separately.

If substituting a tile provider, configure its URL and visible attribution together. Keep a valid browser Referer, use normal browser caching, and avoid tile prefetch. The default map follows the [OpenStreetMap tile policy](https://operations.osmfoundation.org/policies/tiles/).

The frontend's map settings are embedded at build time. For Docker builds, pass both `--build-arg VITE_MAP_TILE_URL="<tile URL template>"` and `--build-arg VITE_MAP_ATTRIBUTION="<provider attribution>"` to `docker build`. Changing only the running container's environment does not update an already-built frontend.

## Deployment checks

- `/api/health` returns a successful response over HTTPS.
- The frontend loads directly at the public URL, including after refresh.
- Demo mode is visibly labeled and renders all three fixture alternatives.
- Live mode returns location suggestions, real routes, checkpoint forecasts, and the separate corridor result when provider credentials are configured.
- Route details and the slider work at desktop and mobile widths; provider and attribution labels remain visible.
- Missing keys and provider failures produce clear errors without exposing secrets or silently switching to the demo.
- Browser network requests contain no TomTom key; production Django debug output is disabled.

## Submit

Provide the [public repository](https://github.com/xdeelord24/wayfinder-weather-routing), [hosted application](https://xdeelord.pythonanywhere.com), and a 5–10 minute Loom recording. [WALKTHROUGH.md](WALKTHROUGH.md) contains the narration and click sequence, and [RECORDING_CHECKLIST.md](RECORDING_CHECKLIST.md) covers preparation and review. Check the account's recording limit before starting; use your own narration and distinguish synthetic demonstrations from live provider observations.

The recording and final assessment-submission confirmation remain pending. Hosting completion alone is not evidence of submission to the employer.
