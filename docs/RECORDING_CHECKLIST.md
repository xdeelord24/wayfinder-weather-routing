# Record and submit the Wayfinder walkthrough

**Completed:** [Public Loom recording — 6:34](https://www.loom.com/share/c3514d7c216f4ae8b1d43d06f0c0fea8); Loom's Share dialog showed **Public — Anyone can find and view**. Spotter's thank-you page acknowledged the submitted answers on **October 26, 2026, at approximately 10:59 AM Asia/Manila**.

This is a reusable checklist; unchecked items below are prompts for a future recording, not a claim that every manual review was performed. Playback, transcript, and sampled frames were viewed in the signed-in session; anonymous-browser playback and full audio quality were not independently reviewed. At 4:58–5:19 the narration describes No Travel while Mixed conditions remain on screen; this was clarified alongside the Loom link in the submission.

Use this with [WALKTHROUGH.md](WALKTHROUGH.md). The requested video is **5–10 minutes**. **Loom Starter limits each recording to five minutes**; use the compact script for that account. Use the seven-minute version only if the account allows longer recordings. [Loom's recording limits](https://support.atlassian.com/loom/docs/how-long-can-i-record/).

Use your own voice and explain what you can demonstrate. Do not purchase an upgrade just to follow the longer script.

For another recording, check the current account allowance directly before choosing the five- or seven-minute version. **Click “Record a video” and start the recording yourself in Loom**, using your own narration.

## Verified evidence available for the video

- **Live services passed at 08:45 Manila on 26 October:** Chicago → Detroit, 32,000 lb, 50-mile spacing, departure `2026-10-26T01:45:46Z`. Rehearsal and recording need a new future departure.
- **Three routes:** 282.92, 305.20, and 334.85 miles; 23 complete checkpoint forecasts; all sampled route weather Low risk; route 1 recommended.
- **Corridor:** 154 cells, 49 hourly frames, zero unknown cell-hours. These were live adapter/service checks, not proof of a hosted browser session.
- **CI passed:** [run 40252769723](https://github.com/xdeelord24/wayfinder-weather-routing/actions/runs/40252769723), revision `fbd195f`, including 47 tests, frontend build, Docker build, and container frontend/API smoke.
- **Host ready:** [Wayfinder on PythonAnywhere](https://xdeelord.pythonanywhere.com/), using a free Beginner account. The 09:00 Manila hosted live check passed six HTTP requests: three distinct live routes, 23 complete checkpoints, 154 cells × 49 frames, and zero unknown cell-hours.
- **Demo/assets passed:** all three scenarios returned 192 cells × 49 frames. Hosted smoke checks also passed after the map-tile fix.
- **Visible browser checks passed:** road tiles, demo checkpoint details, and +0/+24/+48 slider positions. A map-tile referrer-policy correction was verified on the hosted response; all 32 backend tests passed after that correction. A fresh Chicago–Detroit live trip also rendered three alternatives, checkpoint markers, and its corridor.
- **Runtime:** [`fbd195f091cf9359eb160e90db30d3c21bab1dda`](https://github.com/xdeelord24/wayfinder-weather-routing/commit/fbd195f091cf9359eb160e90db30d3c21bab1dda), including the referrer-policy correction. Use [VERIFICATION.md](VERIFICATION.md) for exact evidence scope.
- **Delivered:** the public 6:34 Loom recording and assessment submission are confirmed. Rehearse a fresh live trip if making another recording; the old departure timestamps are historical evidence.

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
- [ ] Click **Record a video** directly yourself in your Loom workspace and use your own narration.
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

## Three submitted links

| Field | Value |
| --- | --- |
| GitHub repository | https://github.com/xdeelord24/wayfinder-weather-routing |
| Hosted application | https://xdeelord.pythonanywhere.com/ — live; hosted API/demo/assets and visible demo controls verified |
| Loom walkthrough | [Public 6:34 recording](https://www.loom.com/share/c3514d7c216f4ae8b1d43d06f0c0fea8) |

All three links were submitted. Spotter's thank-you page explicitly confirmed receipt at approximately **10:59 AM Asia/Manila on October 26, 2026**. The video-link field included the scenario clarification described above.

The invitation sets a four-day deadline and a maximum of 16 working hours; this checklist does not assert how much working time was spent. For future submissions, use the actual invitation timestamp to confirm the cutoff, record time honestly, and retain the receiving success page or receipt.
