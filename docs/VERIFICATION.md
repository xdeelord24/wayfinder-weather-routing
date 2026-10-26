# Verification record

This record distinguishes implementation checks, fixture demonstrations, live providers, and deployment. **Pending means no verified result has been recorded.** Source inspection, tests, and a successful build do not establish live provider or hosted-site behavior.

Live API verification and deployment work resumed with user authorization on **October 26, 2026**. Open-Meteo checks passed. TomTom routing requires the server-side key, and a public deployment and recording have not yet been verified.

The original checks below were performed on **October 24, 2026, Asia/Manila** (October 23 UTC); the October 26 recheck is recorded separately below. The demo uses saved OSRM/OpenStreetMap driving geometry and synthetic weather; demo results do not certify live truck routing.

## October 26 pre-deployment check

- Re-ran all **32 backend tests** and **15 frontend tests**: passed.
- Re-ran TypeScript checking and Vite production build: passed. Vite still reports the existing large MapLibre chunk warning; this is a build-size warning, not a failed build.
- Live Open-Meteo check passed at **00:32:42–00:32:45 UTC** (08:32 Asia/Manila), using two HTTP requests. Three actual US coordinates had complete weather at departure, +1, +24, and +48 hours, with no warnings. These are weather probes, not claimed truck-route checkpoints.
- The provider's HTTP Date was **26 October 2026 00:32:46 UTC**, and current-weather time was 00:30 UTC, corroborating the execution clock.
- Command: `.venv\Scripts\python.exe scripts/verify_live.py`. Local evidence: `output/live-verification/20261026T003242Z-weather.json` (excluded from Git).
- Full routing check command, once configured: `.venv\Scripts\python.exe scripts/verify_live.py --live-plan`. Hosted HTTP/browser behavior still requires separate checks.

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
| Live TomTom location search and truck routing | Pending server-side key | Record actual trip, UTC timestamp, and distinct route count after live execution. |
| Live Open-Meteo forecasts at actual coordinates | Passed October 26 | Three US coordinates, four requested times through +48 hours, no warnings; evidence above. Route-checkpoint integration remains pending TomTom. |
| Live three-route example | Pending | Record origin, destination, departure, cargo, spacing, and distinct alternatives. |
| Hosted frontend and `/api/health` | Pending Render account access | Record public URL, deployment revision, and check time. |
| Hosted live planning and corridor request | Pending deployment and key | Record successful live request plus visible route and corridor results. |
| Public repository | Verified public | [xdeelord24/wayfinder-weather-routing](https://github.com/xdeelord24/wayfinder-weather-routing), branch `main`; initial published revision `a31400fe4fa33e78c64267e76e6676f5f8b5c166`. A 53-file staged scan excluded the assessment PDF and `.env` and found no actual secret. |
| Loom walkthrough | Pending | Recording URL; verify narration and coverage. |

## Evidence notes

Browser screenshots are stored locally in `output/playwright/`, which is excluded from Git; the selected repository preview is [assets/demo-preview.png](assets/demo-preview.png). The repository is public and revision `cb8ae01` passed CI, including the container HTML/assets checks. Live Open-Meteo results are recorded separately above; TomTom, hosted-site, and recording completion have not been asserted. Documentation and verification-script changes do not change the application runtime.
