# Deployment and submission

Wayfinder is packaged as one Docker web service: the frontend builds during image creation, and Django serves the resulting assets and API. No persistent trip database is required.

Deployment status is tracked in [VERIFICATION.md](VERIFICATION.md). The presence of a Dockerfile or Render configuration does not mean a deployment exists.

Hosted deployment is currently deferred at the user's request. These instructions remain available for a later deployment; the current delivery focuses on the local demo.

## Prepare the repository

1. Run the local tests and frontend build and record their results.
2. Confirm `.env`, API credentials, virtual environments, local artifacts, and the supplied assessment PDF are excluded from Git.
3. Publish the source to a public GitHub repository. Include `.env.example` containing placeholders only.
4. Check the published files, then use that repository as the Render deployment source.

## Render Free

1. Create a Render Web Service from the repository, using its Dockerfile and the Free instance type. If using the repository's `render.yaml`, review the generated service settings before creating the service.
2. Set `TOMTOM_API_KEY` as a secret in Render. The Blueprint generates `DJANGO_SECRET_KEY`, sets `DJANGO_DEBUG=false`, and allows `.onrender.com` hosts through `DJANGO_ALLOWED_HOSTS`. If configuring manually, use the service's real hostname. Add any custom domain to the allowed hosts before using it.
3. Use `/api/health` as the health-check path. The service must bind to `0.0.0.0` and Render's `PORT`.
4. Deploy, open the public URL, and verify the React application and health endpoint. Then separately verify a live plan and corridor forecast.
5. Record the URL and deployed revision in the verification record and your submission.

Render Free currently spins down after 15 minutes without inbound traffic; the next request may take about a minute while it starts. Its filesystem is ephemeral, and usage limits apply. This is suitable for an assessment preview; do not rely on local files for persistent state. See [Render's free-service documentation](https://render.com/docs/free).

## Runtime configuration

Use `.env.example` as the authoritative list of supported names. The TomTom key must be available only to the backend. Do not place it in a frontend `VITE_` environment variable, source code, screenshots, or submission text.

The included command runs Gunicorn with one worker and eight threads. Keep one worker while using the local-memory plan cache: multiple worker processes would not share plan IDs. Plans expire after one hour or disappear when the process restarts; an unavailable plan requires a new planning request. A multiworker deployment should first move this cache and throttling state to a shared service.

For an optional local container check, use Docker Desktop in Linux-container mode:

```powershell
docker build -t wayfinder .
docker run --rm -p 8000:8000 --env-file .env wayfinder
```

Open `http://localhost:8000` and `http://localhost:8000/api/health`. These commands validate the container locally; Render must still be checked separately.

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

Provide the public repository URL, verified hosted URL, and a 5–10 minute Loom recording. [WALKTHROUGH.md](WALKTHROUGH.md) contains a seven-minute script. Use your own narration and Loom account, and distinguish fixture demonstrations from live provider evidence.

If deployment or live access has not been completed, label it pending and provide the local setup instructions. Do not describe local execution as a hosted application.
