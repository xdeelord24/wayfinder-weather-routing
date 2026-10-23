# Seven-minute walkthrough

Record this with your own narration. Replace the verification placeholders with results from [VERIFICATION.md](VERIFICATION.md), and mention only checks you actually completed. The fixture demo is suitable for a repeatable presentation; identify it explicitly.

| Time | Show | Suggested narration |
| --- | --- | --- |
| 0:00–0:35 | Landing view and trip form | “I built Wayfinder to compare truck routes using the weather expected when the truck reaches each part of the trip. The goal is to make the recommendation understandable, including when none of the routes qualifies.” |
| 0:35–1:15 | Demo label; Chicago → Detroit inputs; cargo and checkpoint spacing | “This is the repeatable demo: three saved OSRM driving routes with synthetic weather. They follow real road geometry, but the snapshot does not verify truck restrictions. Live mode uses TomTom and Open-Meteo. Departure uses the origin's timezone, cargo affects the weather rules, and checkpoint spacing controls the sampling detail.” |
| 1:15–2:15 | Route cards; select each route; show recommendation reason | “Each route reports travel time and estimated miles in each severity. A No Travel checkpoint makes a route ineligible. Among the remaining routes, the comparison prioritizes Severe exposure, then High exposure, then average risk, and finally travel time.” |
| 2:15–3:00 | Select a checkpoint; point out ETA, wind, rain, snow, and reasons | “This forecast corresponds to the truck's estimated arrival here. Arrival times follow the routing provider's cumulative time along the route. The worst applicable weather condition determines the checkpoint risk, including the assessment's cargo-related wind rules.” |
| 3:00–3:50 | Forecast overlay and slider at +0, +24, and +48 hours | “This is a separate view of the corridor at a chosen time. All 49 hourly frames load together, so scrubbing the slider changes colors locally. It doesn't change the route recommendation, which still uses each checkpoint's arrival time.” |
| 3:50–4:30 | Change checkpoint spacing and show a hazard scenario or unavailable state | “Checkpoint spacing trades sampling detail for provider work. Missing weather is shown as unavailable and cannot improve a route's score. If every route is ineligible, the app explains that instead of naming a winner.” |
| 4:30–5:25 | README architecture diagram and risk table | “The React frontend handles the form and map. Django keeps the provider key private, normalizes forecasts, samples the routes, and computes risk. I separated these responsibilities so the risk rules can be tested without network access.” |
| 5:25–6:20 | Actual test output and verification record | “The tests cover exact risk boundaries, strict cargo cutoffs, exposure-mile totals, ETA interpolation, and ranking. Here are the checks I ran. I record fixture checks separately from real provider and deployed-site checks.” |
| 6:20–7:00 | Return to application; show mobile layout if verified | “The main tradeoffs are sampled weather, a bounded corridor grid, and forecasts limited by the provider's horizon. Next I would add vehicle dimensions, a more complete trip schedule, and production monitoring. The repository includes setup, deployment instructions, and the exact assumptions behind the score.” |

## Before recording

- Start the backend and frontend, open the demo, and wait for the map tiles and overlay to settle.
- Use the same window size throughout the desktop portion; enlarge the browser text if labels are difficult to read in the recording.
- Pick a checkpoint with an understandable risk reason. Rehearse the route and slider changes once.
- Prepare the README and the actual test output in separate tabs. Hide `.env`, terminal history containing secrets, and provider dashboards with API keys.
- If showing live mode, use verified inputs and state the observation time. If live access is unavailable, keep the visible demo label and say so.
- If using Render Free, open the deployed site ahead of recording to allow for its idle cold start. A successful local run is not a hosted-site check.

## Interview discussion notes

**Why mileage weighting?** A simple average over checkpoints gives endpoint samples too much influence and changes unfairly with sampling density. Midpoint boundaries partition the route, so every mile contributes once.

**Why not score a route from the slider?** The slider asks “what does the corridor look like at this time?” Routing asks “what does the truck encounter at each arrival time?” Keeping those separate avoids presenting a stationary snapshot as trip exposure.

**Why not always return three routes?** The routing provider may not have three materially distinct alternatives. The app makes a bounded set of attempts, deduplicates results, and reports a shortfall.

**Why not infer unknown weather?** Treating missing forecasts as clear weather would make incomplete routes appear safer. Missing required checkpoint forecasts exclude a route from recommendation while preserving the available information.

**Why are load thresholds strict?** The assessment says greater than 30,000 lb and greater than 40,000 lb. Boundary tests ensure equality does not trigger escalation.

**What would production change?** Use a suitable commercial forecast/tile agreement, durable shared caching and rate limits, provider monitoring, explicit vehicle attributes, and richer trip scheduling. These are follow-on improvements, not claims about this assessment build.

## Submission items

- Public repository URL: pending publication.
- Hosted application URL: deployment deferred at the user's request.
- Loom recording URL: pending recording with your narration and account.
