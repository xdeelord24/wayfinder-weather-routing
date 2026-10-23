# Verification record

This record distinguishes implementation checks, fixture demonstrations, live providers, and deployment. **Pending means no verified result has been recorded.** Source inspection, tests, and a successful build do not establish live provider or hosted-site behavior.

The user chose to continue with the demo. Live TomTom verification and hosted deployment are **deferred by request**, rather than prerequisites for the current delivery.

Recorded checks below were performed on **October 24, 2026, Asia/Manila** (October 23 UTC). The demo uses saved OSRM/OpenStreetMap driving geometry and synthetic weather; these results do not certify live truck routing.

## Automated checks

| Check | Status | Evidence |
| --- | --- | --- |
| Backend unit and API tests | Passed: 32 tests | `.venv\Scripts\python.exe backend/manage.py test routing.tests` |
| HTTP fixture smoke test | Passed | `.venv\Scripts\python.exe scripts/smoke.py http://127.0.0.1:8001`; results below. |
| Frontend type checking and production build | Passed | `npm.cmd run build` in `frontend/` |
| Frontend behavior tests | Passed: 15 tests | `npm.cmd test` in `frontend/`; API and map are mocked in component tests. |
| npm dependency audit | Passed: 0 reported vulnerabilities | `npm.cmd audit` in `frontend/`; this is a dependency audit, not a complete security review. |
| Local frontend and API on one origin | Passed | Built frontend served by Django with `DJANGO_DEBUG=false` at `http://127.0.0.1:8001`. |
| Desktop browser workflow | Passed for recorded scenarios | Playwright at 1280×720: slider traversal, clear/blocked flows, 10-mile selection, and checkpoint details. |
| Mobile browser workflow | Pending final checks | Final responsive-layout verification is in progress. |
| Docker image and container startup | Pending CI | Workflow builds the image and runs the HTTP smoke test against its container. No successful run recorded yet. |
| GitHub Actions run | Pending | Workflow configured; repository publication and successful run still need confirmation. |

## Scenario evidence

The latest HTTP smoke check used a 32,000 lb cargo load and returned:

| Scenario | Checkpoint spacing | Routes | Corridor cells | Cells changing risk between +0 and +48 hours | Recommendation |
| --- | --- | --- | --- | --- | --- |
| Mixed | 25 miles | 3 | 192 | 70 | `route-3` |
| Clear | 10 miles | 3 | 192 | 0 | `route-1` |
| Blocked | 50 miles | 3 | 192 | 0 | None; all routes ineligible |

All three responses contained 49 frames. Assertions checked checkpoint order, final checkpoint/arrival agreement, mileage totals, eligibility, and corridor limits. This samples each scenario and each spacing option once; it is not the full nine-combination matrix.

The test suites cover weather thresholds, strict cargo cutoffs, maximum combined hazard, unavailable forecasts, midpoint exposure, nonuniform checkpoint timing, duplicate alternatives, bounded provider attempts, missing-key errors, plan expiry, origin timezone handling, and daylight-saving gaps/repeated hours. Provider behavior in these tests uses fixtures or mocks. Independent Python probes also checked a route ending exactly on its checkpoint interval and the km/h, mm, and cm conversions.

The recorded desktop Playwright traversal moved through **all 49 slider positions in 1,268 ms**. The browser's recorded API resource count stayed **3 before / 3 after**, the map retained the same canvas, and the recommendation stayed unchanged. This is a local observation, not a cross-device performance guarantee. Clear and blocked form submissions and checkpoint details were also exercised against the local Django service.

## Live and submission checks

| Check | Status | Evidence to record |
| --- | --- | --- |
| Live TomTom location search and truck routing | Deferred by request | Resume with a server-side key; record actual trip, UTC timestamp, and distinct route count. |
| Live Open-Meteo checkpoint forecasts | Deferred with live mode | Later record request time, returned forecast range, and sample unit/arrival-time comparison. |
| Live three-route example | Deferred by request | Later record origin, destination, departure, cargo, spacing, and distinct alternatives. |
| Hosted frontend and `/api/health` | Deferred by request | Later record public URL, deployment revision, and check time. |
| Hosted live planning and corridor request | Deferred by request | Later record successful live request plus visible route and corridor results. |
| Public repository | Pending | Repository URL and published revision; verify no private files or credentials. |
| Loom walkthrough | Pending | Recording URL; verify narration and coverage. |

## Evidence notes

Browser screenshots are stored locally in `output/playwright/` and are excluded from Git. No live-provider, hosted-site, repository-publication, or recording completion has been asserted in this record. Update pending rows only after their corresponding checks complete.
