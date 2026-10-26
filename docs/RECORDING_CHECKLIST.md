# Record and submit the Wayfinder walkthrough

Use this with [WALKTHROUGH.md](WALKTHROUGH.md). The requested video is **5–10 minutes**. **Loom Starter limits each recording to five minutes**; use the compact script for that account. Use the seven-minute version only if the account allows longer recordings. [Loom's recording limits](https://support.atlassian.com/loom/docs/how-long-can-i-record/).

Use your own voice and explain what you can demonstrate. Do not purchase an upgrade just to follow the longer script.

Loom is signed in to the **jgmolinawork** workspace and displayed a **14-day trial** on 26 October 2026. Check its recorder allowance directly before deciding between the five- and seven-minute versions. The browser security policy blocked automated use of Loom's recording button, so **click “Record a video” and start the recording yourself in Loom**. No recording or upload is confirmed yet.

## Verified evidence available for the video

- **Live services passed at 08:45 Manila on 26 October:** Chicago → Detroit, 32,000 lb, 50-mile spacing, departure `2026-10-26T01:45:46Z`. Rehearsal and recording need a new future departure.
- **Three routes:** 282.92, 305.20, and 334.85 miles; 23 complete checkpoint forecasts; all sampled route weather Low risk; route 1 recommended.
- **Corridor:** 154 cells, 49 hourly frames, zero unknown cell-hours. These were live adapter/service checks, not proof of a hosted browser session.
- **CI passed:** [run 40250357867](https://github.com/xdeelord24/wayfinder-weather-routing/actions/runs/40250357867), revision `20b2528`, including 47 tests, frontend build, Docker build, and container frontend/API smoke.
- **Host ready:** [Wayfinder on PythonAnywhere](https://xdeelord.pythonanywhere.com/), using a free Beginner account. The 09:00 Manila hosted live check passed six HTTP requests: three distinct live routes, 23 complete checkpoints, 154 cells × 49 frames, and zero unknown cell-hours.
- **Demo/assets passed:** all three scenarios returned 192 cells × 49 frames. Hosted smoke checks also passed after the map-tile fix.
- **Visible browser checks passed:** road tiles, demo checkpoint details, and +0/+24/+48 slider positions. A map-tile referrer-policy correction was verified on the hosted response; all 32 backend tests passed after that correction. A fresh Chicago–Detroit live trip also rendered three alternatives, checkpoint markers, and its corridor.
- **Runtime:** baseline `20b2528` plus the October 26 referrer-policy correction. Use [VERIFICATION.md](VERIFICATION.md) for the final revision and exact evidence scope.
- **Still pending:** your Loom recording, playable share URL, and confirmed assessment submission. Rehearse a fresh live trip before narrating its visible result.

## Before recording

- [ ] Open [https://xdeelord.pythonanywhere.com/](https://xdeelord.pythonanywhere.com/) and wait for startup, map tiles, route cards, and corridor frames.
- [ ] Read the current revision and evidence scope in [VERIFICATION.md](VERIFICATION.md). Hosted live API, demo/assets, and visible demo controls have passed.
- [ ] Select **Live planning** and choose **Chicago, IL → Detroit, MI** from location suggestions; enter **32,000 lb** and **Every 50 mi**.
- [ ] Set a fresh future departure within the next 48 hours, using the form's displayed **America/Chicago** timezone. Enter Chicago local time, not Manila time. Approximately one hour ahead leaves time for rehearsal.
- [ ] Click **Find safest routes**; wait for route and corridor results. Note actual route count and check time. Check that departure is still future before the final take; the recorded 26 October verification timestamp is historical evidence.
- [ ] Rehearse Mixed conditions with 32,000 lb / 25 miles and No travel conditions with 50-mile spacing. Identify an easy-to-explain checkpoint.
- [ ] Open only the hosted app, public README, relevant code, and current verification evidence. Hide email, other client projects, `.env`, API keys, and terminals containing secrets.
- [ ] Use a browser window large enough to show route cards and map together. Check text readability in the recording preview; avoid continuous zoom changes.
- [ ] In your own Loom account, choose screen recording and your microphone. Camera is optional unless Spotter separately requires it. Select only the relevant window or display.
- [ ] Click **Record a video** directly yourself in the jgmolinawork Loom workspace; do not attempt to bypass the browser's blocked automated recording action.
- [ ] Make a short microphone test and play it back. Confirm the recording allowance displayed by your account and select the matching script; the assessment requires at least five minutes.

## Five-minute recording (Starter)

Finish speaking by **4:50**. Leave the final app view visible until the recorder stops at **5:00**, then verify the saved duration. Do not trim it below the assessment's five-minute minimum. The Starter countdown runs from 5:00 remaining to 0:00 remaining.

| Elapsed time | Action |
| --- | --- |
| 0:00–0:30 | Introduce Wayfinder and show trip inputs. |
| 0:30–1:00 | Explain verified live evidence, then identify the demo data. |
| 1:00–1:50 | Compare all three routes and explain eligibility and ranking. |
| 1:50–2:40 | Show checkpoint ETA/weather, reasons, and cargo thresholds. |
| 2:40–3:30 | Toggle heatmap; show +0, +24, +48; animate briefly. |
| 3:30–4:00 | Change spacing and show No travel conditions. |
| 4:00–4:50 | Show architecture and verification, state limits, return to app. |
| 4:50–5:00 | Leave the final app view visible until the automatic stop. |

## Extended recording (only if the account permits)

| Time | Action |
| --- | --- |
| 0:00 | Introduce Wayfinder and show the hosted URL. |
| 0:35 | Demonstrate the verified live trip; then clearly switch to the labeled repeatable demo. |
| 1:30 | Select all three demo routes and explain eligibility and ranking. |
| 2:30 | Open a checkpoint; show arrival-time weather and the strict cargo thresholds. |
| 3:30 | Toggle the weather layer, show +0 / +24 / +48, play briefly, then pause. |
| 4:35 | Show different checkpoint spacing and No travel conditions. |
| 5:20 | Brief architecture/code tour and current verification evidence. |
| 6:20 | State limits, return to the working app, and finish. |

If a real provider request fails during the take, describe the visible result honestly. Rehearse before re-recording; do not disguise demo data as live results. Pause for slow responses rather than rushing the explanation. You can trim empty waiting time without removing evidence of what happened.

## After recording

- [ ] Suggested title: **Wayfinder — Weather-Aware Truck Routing | Jundee Molina**.
- [ ] Saved duration is between 5 and 10 minutes. For the Starter take, verify **5:00**, with the final view held for the last ten seconds. Audio is understandable and labels are readable.
- [ ] Playback includes three routes, checkpoint ETA/weather, cargo rules, 0–48-hour controls, no-eligible-route behavior, and a short code/testing explanation.
- [ ] No confidential tabs, credentials, private data, or unsupported claims are visible or spoken.
- [ ] Copy the final Loom share link. Verify playback using an unauthenticated window and the intended sharing permissions.
- [ ] Open the repository and hosted app without an account. Confirm the demo loads and live behavior matches the verification record.

## Three links to submit

| Field | Value |
| --- | --- |
| GitHub repository | https://github.com/xdeelord24/wayfinder-weather-routing |
| Hosted application | https://xdeelord.pythonanywhere.com/ — live; hosted API/demo/assets and visible demo controls verified |
| Loom walkthrough | **Add final playable share URL** |

The hosted link is ready. The assessment itself remains pending until the Loom link is ready and Spotter's submission is confirmed.

The invitation sets a four-day deadline and a maximum of 16 working hours. Use the actual invitation timestamp to confirm the cutoff and record time honestly; this checklist does not assert how much time has been spent. Submit once the links are ready, then retain the success page or receipt with its timestamp. Do not mark the assessment complete based only on a prepared form.
