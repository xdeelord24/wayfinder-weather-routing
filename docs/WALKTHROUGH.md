# Spotter walkthrough: five-minute and seven-minute options

**Delivered video:** [Public Loom walkthrough — 6:34](https://www.loom.com/share/c3514d7c216f4ae8b1d43d06f0c0fea8). **Submission confirmed:** October 26, 2026, approximately 10:59 AM Asia/Manila; Spotter's thank-you page acknowledged receiving the answers.

The sequences below remain reusable rehearsal guides. See [VERIFICATION.md](VERIFICATION.md) for the submitted recording's review scope and the clarification accompanying its No Travel segment.

Record with your own voice. Use this as a speaking guide, with your usual wording and pauses while the app responds. The assessment requests **5–10 minutes**. Use the **exactly-five-minute option for Loom Starter**, or aim for 7–8 minutes if the account permits longer recording. Spend most of the video on route logic and the interactive map; those make up 80% of the rubric. Keep the code tour short.

For another recording, prepare with [RECORDING_CHECKLIST.md](RECORDING_CHECKLIST.md) and refresh time-sensitive evidence below.

| Recording fact | Verified result |
| --- | --- |
| Hosted URL | [xdeelord.pythonanywhere.com](https://xdeelord.pythonanywhere.com/) — **ready for recording** on a free PythonAnywhere Beginner account. Hosted live API, demo, and asset checks passed; visible demo map/checkpoint/slider checks passed. |
| Live example | Chicago → Detroit; 32,000 lb; 50-mile spacing; departure `2026-10-26T01:45:46Z`. Three distinct routes: 282.92, 305.20, and 334.85 miles. Use a new future departure when recording. |
| Live check time | **Passed 26 October 2026, 08:45 Manila** (00:45 UTC): live adapters/services; hosted HTTP and browser verification remain separate. |
| Deployment revision | Submitted runtime [`fbd195f091cf9359eb160e90db30d3c21bab1dda`](https://github.com/xdeelord24/wayfinder-weather-routing/commit/fbd195f091cf9359eb160e90db30d3c21bab1dda), including the map-tile referrer-policy correction. |
| Live weather and corridor | All 23 checkpoint forecasts available; 154 corridor cells × 49 frames; zero unknown cell-hours. All sampled route weather was Low risk, and `route-1` was recommended. |
| Test evidence | [CI run 40252769723](https://github.com/xdeelord24/wayfinder-weather-routing/actions/runs/40252769723) passed at `fbd195f`: 47 tests, frontend build, Docker build, and container frontend/API smoke. Hosted verification is recorded separately. |
| Preliminary weather check | Open-Meteo responded at three US locations on 2026-10-26 at 00:32 UTC (08:32 Manila). This does not establish TomTom routing or hosted deployment. |
| Hosted live check | **Passed 09:00 Manila, 26 October:** six HTTP 200 responses, three distinct live routes, 23 complete checkpoint forecasts, 154 cells × 49 frames, zero unknown cell-hours. |
| Hosted demo and assets | All three scenarios passed with 192 cells × 49 frames. Hosted smoke checks passed again after the map-tile correction. |
| Visible browser checks | Road tiles visible; demo checkpoint details and +0/+24/+48 slider positions verified. A fresh hosted Chicago–Detroit live trip also rendered all three routes, checkpoint markers, and its corridor after the fix. |

The live evidence is recorded locally in `output/live-verification/20261026T004545Z-plan.json`; its scope is **live adapters and services, not hosted HTTP or browser verification**. The checked weather was Low risk, so use the labeled synthetic demo to demonstrate hazards.

Hosted evidence is recorded separately in `output/live-verification/20261026T010039Z-hosted.json` and `output/live-verification/20261026T0100Z-hosted-demo-smoke.json`. A visible road-tile issue was fixed by setting `SECURE_REFERRER_POLICY` to `strict-origin-when-cross-origin`; the hosted header and visible tiles were rechecked, all 32 backend tests passed, and hosted smoke checks passed after the fix. There is no need to spend recording time on this implementation detail unless asked.

For future recordings, check the recorder's current duration allowance before choosing a version and **click “Record a video” yourself directly in Loom**. Use your own narration and verify the saved recording rather than assuming the rehearsal timing matches it.

## Set up the hosted recording

Open [Wayfinder](https://xdeelord.pythonanywhere.com/) and wait for the initial demo map, route cards, and forecast frames. For the live portion, select **Live planning**, choose **Chicago, IL** and **Detroit, MI** from the suggestions, enter **32,000 lb** and **Every 50 mi**, then choose a new future departure within the next 48 hours. The form uses the origin's displayed **America/Chicago** timezone: enter Chicago local time, not Manila time. A departure about one hour ahead in that displayed timezone gives time to rehearse. Click **Find safest routes** and wait for both route and corridor results. Recheck the departure before the final take; do not reuse the dated verification timestamp after it has passed.

Keep the actual hosted URL visible at the opening and closing. Hosted live HTTP checks have passed. Rehearse the fresh browser trip before recording and describe what is actually visible; do not claim all possible trips or weather conditions were tested.

## Five-minute version for Loom Starter

Loom Starter stops recording at **5:00**, which is also the assessment's minimum duration. Use this compact version if the recorder shows that limit. Finish speaking by **4:50**, leave the final app view visible, and let the recorder reach **5:00**. Check the saved duration and do not trim it below five minutes. Confirm the current account allowance; no upgrade is needed to use this compact script. [Loom recording limits](https://support.atlassian.com/loom/docs/how-long-can-i-record/).

The main narration below is approximately 540 words. Practice it once with a timer, speaking naturally while performing the actions. Have results loaded before recording so provider wait time does not consume the five-minute take.

### 0:00–0:30 — Introduction and inputs

**Show:** Hosted URL and ready route view. Point to departure, cargo, and spacing.

> Hi, I’m Jundee. This is Wayfinder, my weather-aware truck-routing assessment. It compares the weather a truck is expected to encounter along alternative routes, then explains which route qualifies for recommendation.
>
> The inputs are origin, destination, departure, cargo load, and checkpoints every 10, 25, or 50 miles. Departure uses the origin’s timezone. The interface keeps weather units visible so the comparison is easy to follow.

### 0:30–1:00 — Live evidence and demo distinction

**Show:** A fresh Chicago → Detroit result in the hosted app with 32,000 lb and 50-mile spacing, rehearsed before recording, or the dated hosted verification record. Then show **Explore demo → Mixed conditions**, 32,000 lb, 25-mile spacing.

> Live mode uses TomTom for geocoding and truck routing, with Open-Meteo forecasts. The provider key stays on the server. The verification record states which live checks have passed. Live alternatives are deduplicated; if fewer than three exist, the app reports that shortfall.
>
> For reproducible hazards, I’m using the labeled demo: three saved OSRM driving routes with synthetic weather. These are not current forecasts or verified truck-restriction data.

**If showing the dated evidence, say:** “The October 26 hosted API check returned three routes and 23 complete checkpoint forecasts, plus 49 corridor forecast frames; all sampled route weather was Low risk.”

**Verification wording:** “The app is deployed on PythonAnywhere. Hosted live API checks passed, along with the demo, assets, and visible map controls.” Only describe a fresh live-browser trip as verified after rehearsing it successfully.

### 1:00–1:50 — Three routes and ranking

**Click:** Each route card, then the recommended one. Point to mileage, duration, selected map line, and recommendation reason.

> These cards show distance, duration, arrival, and estimated miles in each risk band. Selecting a card highlights its route and checkpoints on the map.
>
> A route is ineligible if any required checkpoint has No Travel conditions or an unavailable forecast. Eligible routes rank by Severe miles first, then High miles, then distance-weighted average risk, and finally travel time.
>
> Each checkpoint represents the road halfway toward its neighbors. Those sections add up to the complete route mileage. This avoids overcounting endpoints or averaging samples without considering distance. Travel speed alone cannot compensate for a route being ineligible under these rules.

### 1:50–2:40 — Arrival weather and cargo

**Click:** A rehearsed checkpoint. Point to ETA, values, risk, and reason.

> This checkpoint’s forecast is matched to its estimated arrival, using cumulative travel time from the route. Wind is measured in miles per hour; rain and snow in inches per hour. The worst applicable condition sets its risk. The panel also lists which condition triggered the risk and how much road it represents.
>
> Cargo changes the wind rules. Wind from 45 to below 55 becomes No Travel above 30,000 pounds. Wind from 35 to below 45 becomes Severe above 40,000 pounds. Exactly those load thresholds do not trigger escalation. Wind of 55 or more means No Travel at every load.

### 2:40–3:30 — Interactive forecast map

**Click:** Close checkpoint; toggle **Weather layer**; move slider through +0, +24, +48; play briefly, then pause.

> The corridor layer lets me inspect the weather around all routes. I can hide it, change the hour, or play the forecast.
>
> There are 49 hourly frames, from departure through 48 hours later. They load together, so moving the slider changes colors locally instead of fetching weather for every movement. The bounded grid reports its resolution, making its level of detail visible.
>
> This is a corridor snapshot at one time. Recommendations still use each checkpoint’s arrival-time weather, so scrubbing does not change the ranking.

### 3:30–4:00 — No eligible route

**Click:** Choose **No travel conditions**, **Every 50 mi**, then **Find safest routes**.

> Here I change the checkpoint spacing and select the synthetic No Travel scenario. Every route becomes ineligible, and the app explains why rather than choosing a winner. Missing required forecasts also prevent a recommendation; they are never scored as clear weather. Origin and destination are always sampled.

### 4:00–4:50 — Architecture, evidence, and limits

**Show:** README architecture and current verification record; return to the working app before 4:50.

> React and TypeScript handle the interface and MapLibre map. Django owns provider calls, validation, sampling, and scoring. The risk functions are separate from network calls, with tests for boundaries, arrival times, exposure totals, and ranking. The production design serves both frontend and API together from one origin.
>
> This record distinguishes tests, demo checks, live providers, and deployment. Weather remains sampled; vehicle dimensions and driver breaks are future improvements. The repository documents these assumptions and setup. Thank you for reviewing Wayfinder.

### 4:50–5:00 — Hold the final view

Leave the app, its URL, and route comparison visible while Loom reaches its five-minute stop. Do not end at 4:50, and confirm the saved recording duration before submission.

## Extended version — about seven minutes

Use the following sequence only if the account permits recording longer than five minutes.

## 0:00–0:35 — Purpose and trip inputs

**Show:** The hosted app with its URL visible. Start with the map and route comparison visible together.

**Say:**

> Hi, I’m Jundee. This is Wayfinder, my weather-aware truck-routing assessment. It compares routes using the weather expected when the truck reaches each checkpoint. I’ll show the route comparison, explain the risk calculation, and then demonstrate the 48-hour weather map.
>
> The inputs are the starting point, destination, departure, cargo load, and checkpoint spacing. Departure uses the origin’s timezone. Checkpoints can be every 10, 25, or 50 miles.

## 0:35–1:30 — Live path and repeatable demo

**Click:** **Live planning**. Select Chicago and Detroit from the location suggestions. Use a fresh future departure within the next 48 hours, 32,000 lb, and **Every 50 mi**, matching the verified trip's load and spacing. Click **Find safest routes**. Wait for route cards and the corridor forecast. The previously checked departure is historical evidence, not an input to reuse after it passes.

**Say only after this live request works:**

> This request uses TomTom for geocoding and truck routing, and Open-Meteo for forecasts. The API key stays on the Django server. Here are the actual alternatives returned for this trip, each with its own travel time and checkpoint arrival times.
>
> The provider may return fewer than three distinct alternatives. The app makes bounded fallback requests and shows a warning if it still cannot find three.

**Verified example to mention if useful:** “The October 26 service check returned three routes of about 283, 305, and 335 miles, with 23 complete checkpoint forecasts. Its corridor had 154 cells across 49 hourly frames, with no unknown values.” State this as the dated check, not a promise that every fresh request produces identical weather or distances.

**Click:** **Explore demo**, choose **Mixed conditions**, keep 32,000 lb and 25-mile spacing, then click **Find safest routes**.

> I’ll use the labeled demo for the hazard examples so they are reproducible. It contains three saved OSRM driving routes with synthetic weather. These are real road shapes, but the demo does not verify truck restrictions or show current forecasts.

**If live verification remains unavailable:** Replace the live-success paragraph with the specific remaining limitation and demonstrate the labeled demo. Do not describe a demo-only deployment as completed live integration.

## 1:30–2:30 — Three routes and recommendation

**Click:** Select each of the three route cards, then return to the recommended route. Point to the selected line, duration, distance, arrival, and Severe/High mileage. Keep the recommendation explanation visible.

**Say:**

> Selecting a card highlights that route on the map. The cards show distance, duration, arrival, and estimated mileage in each risk band.
>
> First, a route is excluded if any required checkpoint has No Travel conditions or missing forecast coverage. Among eligible routes, I compare Severe miles first, then High miles, then distance-weighted average risk, and finally travel time. The quickest route is not automatically the recommendation.
>
> Each checkpoint represents the road halfway toward its neighbors. Those sections add up to the route’s total mileage. This avoids counting the endpoints as full intervals or simply averaging checkpoint scores.

## 2:30–3:30 — Arrival-time weather and cargo rules

**Click:** A checkpoint with a clear non-Low risk reason, identified during rehearsal. Point to its mile position, ETA, weather values, explanation, and represented mileage.

**Say:**

> This panel shows the forecast at this checkpoint’s estimated arrival, not just the weather at departure. The ETA follows the routing provider’s cumulative travel time along the route.
>
> Wind is in miles per hour; rain and snow are in inches per hour. The highest applicable weather risk becomes the checkpoint’s risk. The assessment also changes wind risk based on cargo.
>
> Wind from 45 to below 55 miles per hour becomes No Travel above 30,000 pounds. Wind from 35 to below 45 becomes Severe above 40,000 pounds. “Above” matters: exactly 30,000 or 40,000 does not trigger its corresponding load escalation. Wind of 55 or more is No Travel at every load.

**Optional:** Replan with a different load only if rehearsal shows a useful change. Describe the actual result; do not promise every checkpoint changes.

## 3:30–4:35 — Map and 0–48-hour forecast

**Click:** Close the checkpoint panel. Toggle **Weather layer** off and on. Move **Forecast hours after departure** to +0, +24, and +48. Play briefly, then pause. Keep routes visible.

**Say:**

> The weather layer covers the corridor around all the routes. These colors show risk at the selected time, from departure through 48 hours later.
>
> The backend returns all 49 hourly frames together. Moving the slider updates the colors locally; it does not request a new forecast for every movement. The corridor grid is bounded to control provider work, and the app reports its resolution.
>
> This map is a snapshot of the corridor at one time. Route ranking still uses the weather at each checkpoint’s arrival. Moving the slider therefore does not change the recommendation.

## 4:35–5:20 — Sampling and no eligible route

**Click:** Set **Every 50 mi**, choose **No travel conditions**, and click **Find safest routes**. Point to the ineligible cards and explanation. If time permits, choose **Clear skies**, set **Every 10 mi**, and replan.

**Say:**

> Checkpoint spacing controls how often the route is sampled. Origin and destination are always included. Closer samples provide more detail but require more forecast work.
>
> In this synthetic No Travel scenario, every route is ineligible. The app explains that instead of presenting a winner. Missing required forecasts are also unavailable, rather than clear weather. The Clear skies scenario lets me check eligible-route behavior separately.

## 5:20–6:20 — Architecture and verification

**Show:** The public README architecture diagram, then briefly `backend/routing/domain.py` (`assess_weather` and `recommend`). Finish on current [verification evidence](VERIFICATION.md) or actual successful CI/test output for the deployed revision.

**Say:**

> React and TypeScript handle the form, comparison cards, and MapLibre map. Django validates input, calls providers, samples the route, and calculates risk. The production service serves both the built frontend and the API.
>
> Risk and ranking functions are separated from network calls so their rules can be tested directly. Tests cover threshold boundaries, strict cargo cutoffs, checkpoint timing, exposure-mile totals, missing forecasts, and recommendation order.
>
> This record separates automated checks, demo behavior, live provider checks, and the hosted deployment. These are the results for the version being shown.

**Read only verified counts and outcomes.** Do not describe old test output as a fresh run or CI as proof of live-provider behavior. Keep credentials and provider dashboards off screen.

## 6:20–7:10 — Limits and closing

**Click:** Return to the hosted app. Restore **Mixed conditions**, 32,000 lb, **Every 25 mi**, then show the recommended route and a checkpoint.

**Say:**

> The main tradeoff is that weather is sampled at checkpoints and corridor cells. It estimates exposure between those locations. The live route uses a truck profile, but full vehicle dimensions, gross vehicle weight, and hazardous-material restrictions are not configured.
>
> Forecast coverage is limited by the provider’s horizon. A route arriving outside that coverage is not recommended. The app does not silently replace a failed live request with demo data.
>
> Further improvements would include a richer vehicle profile, driver breaks, and production monitoring. For this assessment, I focused on visible risk rules, an explainable comparison, and an interactive map. The repository includes setup instructions, assumptions, tests, and deployment details. Thank you for reviewing Wayfinder.

## Useful answers if asked

**Why mileage weighting?** A simple checkpoint average changes with sample density and overweights endpoints. Midpoint sections partition the route so each mile contributes once.

**Why keep the slider separate from scoring?** A map at one timestamp and weather encountered during a moving trip answer different questions. Route scoring follows each arrival time.

**Why not guarantee three live routes?** Some trips have fewer materially different alternatives. The app deduplicates results and reports a shortfall instead of presenting duplicates as different routes.

**What happens when weather is missing?** The checkpoint is Unknown. A route with missing required forecasts is ineligible, and its average risk is unavailable rather than zero.

**What did you use to build it?** Describe the tools and assistance you actually used and the parts you can explain. Do not claim unaided implementation, work hours, or live checks that are not true.

## Submission links

- Public repository: [xdeelord24/wayfinder-weather-routing](https://github.com/xdeelord24/wayfinder-weather-routing).
- Hosted application: [xdeelord.pythonanywhere.com](https://xdeelord.pythonanywhere.com/) — live, with hosted API/demo/assets and visible demo-map checks passed.
- Loom walkthrough: [Public recording — 6:34](https://www.loom.com/share/c3514d7c216f4ae8b1d43d06f0c0fea8), reviewed through transcript and sampled frames, with the disclosed scenario mismatch noted above.
- Assessment submission: **Receipt confirmed October 26, 2026, approximately 10:59 AM Asia/Manila**, through Spotter's thank-you page.

For any future submission, retain the receiving form's success message or employer receipt; a recording, saved form, or clicked button alone does not prove receipt.
