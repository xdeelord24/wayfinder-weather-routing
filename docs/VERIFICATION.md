# Verification record

This record distinguishes implementation checks, fixture demonstrations, live providers, and deployment. **Pending means no verified result has been recorded.** Source inspection, tests, and a successful build do not establish live provider or hosted-site behavior.

Live API verification and deployment work resumed with user authorization on **October 26, 2026**. Full TomTom and Open-Meteo service checks passed, followed by hosted HTTP verification at [xdeelord.pythonanywhere.com](https://xdeelord.pythonanywhere.com). A map-tile referrer-policy issue found during visible checking was corrected, regression-tested, deployed, and verified in the hosted desktop demonstration. Mobile results remain the historical local checks. The Loom recording remains pending.

The original checks below were performed on **October 24, 2026, Asia/Manila** (October 23 UTC); the October 26 recheck is recorded separately below. The demo uses saved OSRM/OpenStreetMap driving geometry and synthetic weather; demo results do not certify live truck routing.

## October 26 pre-deployment check

- Re-ran all **32 backend tests** and **15 frontend tests**: passed.
- Re-ran TypeScript checking and Vite production build: passed. Vite still reports the existing large MapLibre chunk warning; this is a build-size warning, not a failed build.
- Live Open-Meteo check passed at **00:32:42–00:32:45 UTC** (08:32 Asia/Manila), using two HTTP requests. Three actual US coordinates had complete weather at departure, +1, +24, and +48 hours, with no warnings. These are weather probes, not claimed truck-route checkpoints.
- The provider's HTTP Date was **26 October 2026 00:32:46 UTC**, and current-weather time was 00:30 UTC, corroborating the execution clock.
- Command: `.venv\Scripts\python.exe scripts/verify_live.py`. Local evidence: `output/live-verification/20261026T003242Z-weather.json` (excluded from Git).
- Full routing check command, once configured: `.venv\Scripts\python.exe scripts/verify_live.py --live-plan`. Hosted HTTP/browser behavior still requires separate checks.
- [CI run 40250357867](https://github.com/xdeelord24/wayfinder-weather-routing/actions/runs/40250357867) passed at revision `20b2528`, including all 47 tests, frontend build, Docker build, and production-container frontend/API smoke.

### Full live routing and weather result

Command: `.venv\Scripts\python.exe scripts/verify_live.py --live-plan`. Ran **00:45:45–00:45:52 UTC / 08:45 Asia/Manila on October 26**. Local credential-free evidence: `output/live-verification/20261026T004545Z-plan.json`.

| Input or check | Observed result |
| --- | --- |
| Trip | Chicago, Illinois → Detroit, Michigan |
| Departure | 2026-10-26 01:45:46 UTC |
| Cargo and spacing | 32,000 lb; 50 miles |
| Live alternatives | Three distinct routes: 282.92, 305.20, and 334.85 miles |
| Arrival-time forecasts | All 23 checkpoints complete |
| Corridor coverage | 154 cells × 49 hourly frames; zero unknown cell-hours |
| Recommendation | Route 1; all alternatives currently Low risk |
| Provider traffic | Nine HTTP requests in the bounded verification run |

No application fix was needed for this local service check. It verifies the actual backend adapters and services; the hosted HTTP and browser results are recorded separately below. Synthetic demo scenarios remain useful for showing hazards when the live forecasts are all Low.

## October 26 hosted verification

**URL:** [https://xdeelord.pythonanywhere.com](https://xdeelord.pythonanywhere.com). PythonAnywhere runs Python 3.12 with one WSGI worker from `/home/xdeelord/wayfinder`. Production settings use `DJANGO_DEBUG=false`, the exact public hostname, and a private `.env` with permissions `600`; `manage.py check` passed. Disk usage was approximately 218 MiB by `du`, with about 230 MB reported against the 512 MB quota. The free web app's current expiry is November 26, 2026; monthly manual renewal is required.

The initial `wayfinder-pythonanywhere-20261026T004930Z.zip` bundle used application runtime from revision `20b2528`. It included 22 runtime/build files, with credentials and the supplied assessment excluded. The hosted map correction described below is a subsequent runtime settings change.

Command: `.venv\Scripts\python.exe scripts/verify_hosted.py https://xdeelord.pythonanywhere.com`. Ran **01:00:39–01:00:50 UTC / 09:00 Asia/Manila**. Credential-free local evidence: `output/live-verification/20261026T010039Z-hosted.json`.

| Hosted check | Observed result |
| --- | --- |
| Public requests | Six requests, all HTTP 200; no retries |
| Health and frontend HTML | Healthy with routing configured; Wayfinder title and built JS/CSS references present |
| Live location selection | Chicago and Detroit IDs returned by the hosted search endpoints |
| Departure, cargo, spacing | 2026-10-26 02:00:43 UTC; 32,000 lb; 50 miles |
| Live alternatives | Three distinct geometries: 282.92, 305.20 and 334.85 miles |
| Arrival-time forecasts | All 23 checkpoints complete; forecast intervals cover ETAs |
| Mileage and eligibility | Exposure totals conserve route mileage; eligibility matches hazards |
| Corridor | 154 cells × 49 frames; zero unknown cell-hours |
| Recommendation | Route 1; all alternatives Low risk at this observation |

The separate command `.venv\Scripts\python.exe scripts/smoke.py https://xdeelord.pythonanywhere.com --frontend` also passed. It verified two served frontend entry assets with correct content types and nonempty bodies. Mixed/25-mile chose Route 3, clear/10-mile chose Route 1, and blocked/50-mile returned no recommendation. All three demos had 192 cells and 49 frames; the mixed case changed 70 cells between +0 and +48 hours. Evidence: `output/live-verification/20261026T0100Z-hosted-demo-smoke.json`. These checks predate the referrer-policy correction and do not certify map tile rendering.

### Hosted desktop browser verification and map correction

Visible inspection found OpenStreetMap 403 tile placeholders. The hosted page sent Django's default `Referrer-Policy: same-origin`, which suppresses the origin referrer on cross-origin tile requests. The correction sets `SECURE_REFERRER_POLICY="strict-origin-when-cross-origin"`, retaining an origin referrer on HTTPS tile requests without sending the page path. This matches the [OpenStreetMap tile policy](https://operations.osmfoundation.org/policies/tiles/).

The response-header regression assertion failed before this change and passed after it; all 32 backend tests passed. The corrected host returned HTTP 200 with `Referrer-Policy: strict-origin-when-cross-origin`. The deployed settings SHA-256, `28418c3ea2062633ef9996d96189063829822602df3248a79ae299396eafc6ba`, matched the local file.

The hosted demo/assets smoke passed again with the new referrer-header assertion. Evidence: `output/live-verification/20261026T0104Z-hosted-referrer-smoke.json`.

Visible desktop checks confirmed real OpenStreetMap tiles with routes and heatmap; the evidence screenshot is `output/live-verification/pythonanywhere-map-fixed.png`. In the mixed demonstration, selecting the mile-125 checkpoint showed 20.5 mph wind, 0.68 in/hr rain, and Severe risk. Keyboard movement of the actual slider to +0, +24, and +48 hours changed the labels/dates while leaving the recommendation unchanged. A fresh Chicago–Detroit live trip after the correction also visibly rendered three alternatives, checkpoint markers, and the corridor; screenshot: `output/live-verification/pythonanywhere-live-routes.png`. A fresh hosted mobile pass has not been recorded.

## Automated checks

| Check | Status | Evidence |
| --- | --- | --- |
| Backend unit and API tests | Passed: 32 tests | `.venv\Scripts\python.exe backend/manage.py test routing.tests` |
| HTTP fixture smoke test | Passed | `.venv\Scripts\python.exe scripts/smoke.py http://127.0.0.1:8001`; results below. |
| Frontend type checking and production build | Passed | `npm.cmd run build` in `frontend/` |
| Frontend behavior tests | Passed: 15 tests | `npm.cmd test` in `frontend/`; API and map are mocked in component tests. |
| npm dependency audit | Passed: 0 reported vulnerabilities | `npm.cmd audit` in `frontend/`; this is a dependency audit, not a complete security review. |
| Local frontend and API on one origin | Passed | Built frontend served by Django with `DJANGO_DEBUG=false` at `http://127.0.0.1:8001`; smoke `--frontend` verified HTTP 200 HTML/title and both JavaScript/CSS entry assets with their response types/content. |
| Desktop browser workflow | Passed for recorded scenarios | Final Playwright check at 1440×1000; earlier 1280×720 check also exercised clear/blocked flows and 10-mile selection. |
| Mobile browser workflow | Passed for recorded scenarios | Playwright at 390×844: no horizontal page overflow, recommended route first, route/checkpoint selection, and demo/live mode transitions. |
| Docker image and container startup | Passed | CI built the image, started Gunicorn, and passed the demo API smoke test against the container at revision `cb8ae01`. |
| GitHub Actions run | Passed | [Successful run 39989567538](https://github.com/xdeelord24/wayfinder-weather-routing/actions/runs/39989567538): 47 tests, frontend build, Django check/static collection, Docker build, and container frontend/API smoke. |
| Container HTML/assets smoke extension | Passed | The `--frontend` assertions verified HTTP 200 HTML/title and two JavaScript/CSS entry assets with correct response types and nonempty content, both locally and in the CI container. |

## Scenario evidence

The latest HTTP smoke check used a 32,000 lb cargo load and returned:

| Scenario | Checkpoint spacing | Routes | Corridor cells | Cells changing risk between +0 and +48 hours | Recommendation |
| --- | --- | --- | --- | --- | --- |
| Mixed | 25 miles | 3 | 192 | 70 | `route-3` |
| Clear | 10 miles | 3 | 192 | 0 | `route-1` |
| Blocked | 50 miles | 3 | 192 | 0 | None; all routes ineligible |

All three responses contained 49 frames. Assertions checked checkpoint order, final checkpoint/arrival agreement, mileage totals, eligibility, and corridor limits. This samples each scenario and each spacing option once; it is not the full nine-combination matrix.

The test suites cover weather thresholds, strict cargo cutoffs, maximum combined hazard, unavailable forecasts, midpoint exposure, nonuniform checkpoint timing, duplicate alternatives, bounded provider attempts, missing-key errors, plan expiry, origin timezone handling, and daylight-saving gaps/repeated hours. Provider behavior in these tests uses fixtures or mocks. Independent Python probes also checked a route ending exactly on its checkpoint interval and the km/h, mm, and cm conversions.

The final production-build Playwright traversal moved through **all 49 slider positions in 1,148 ms**. The browser's recorded API resource count stayed **3 before / 3 after**, the map retained the same canvas, and the recommendation stayed unchanged. This is a local observation, not a cross-device performance guarantee. Clear and blocked form submissions and checkpoint details were also exercised against the local Django service.

Final desktop/mobile checks reported **zero page errors, zero console errors, and zero console warnings**. At 390×844, the page had no horizontal overflow and showed the recommended route first. Selecting the I-94 route and its mile-25 checkpoint displayed 26.1 mph wind, 0.12 in/hr rain, zero snow, and 25 miles of represented exposure. Switching to live mode without a key cleared the route cards and displayed the missing-key notice; returning to demo worked.

## Live and submission checks

| Check | Status | Evidence to record |
| --- | --- | --- |
| Live TomTom location search and truck routing | Passed October 26 | Real Chicago–Detroit request returned three distinct alternatives; details above. |
| Live Open-Meteo forecasts | Passed October 26 | Three-coordinate weather probe, then all 23 live route checkpoints and 154 × 49 corridor values complete. |
| Live three-route example | Passed October 26 | 32,000 lb, 50-mile spacing, departure 01:45:46 UTC; details above. |
| Hosted frontend assets and `/api/health` | Passed October 26 | Public HTTPS responses and both JS/CSS entry assets verified; details above. |
| Hosted live planning and corridor request | Passed October 26 | Six-request hosted run verified three routes, 23 complete checkpoint forecasts, and 154 × 49 corridor coverage. |
| Hosted visible desktop demo | Passed October 26 | Corrected map tiles, routes/heatmap, mile-125 Severe popup, and actual +0/+24/+48-hour slider controls verified. |
| Hosted mobile UI | Not rechecked | October 24 mobile evidence is local; it is not a fresh hosted mobile run. |
| Public repository | Verified public | [xdeelord24/wayfinder-weather-routing](https://github.com/xdeelord24/wayfinder-weather-routing), branch `main`; initial published revision `a31400fe4fa33e78c64267e76e6676f5f8b5c166`. A 53-file staged scan excluded the assessment PDF and `.env` and found no actual secret. |
| Loom walkthrough | Pending | Recording URL; verify narration and coverage. |

## Evidence notes

Historical browser screenshots are stored locally in `output/playwright/`; the new hosted screenshot and HTTP evidence are under `output/live-verification/`. Both directories are excluded from Git; the selected repository preview is [assets/demo-preview.png](assets/demo-preview.png). The repository is public and revision `20b2528` passed CI, including the container HTML/assets checks. The later referrer-policy correction passed local backend tests, hosted HTTP/header checks, and the recorded desktop demonstration. The Loom recording and final assessment submission have not been confirmed.
