# Push move-alerts — deploy checklist

What's now built vs. what already existed:

**Already live (from before this session):**
- Client subscribe flow (`enableNotifications()`), VAPID public key embedded, `sw.js` already has `push` + `notificationclick` handlers.

**New in this drop:**
- `worker.js` — `/push-subscribe` (stores subscriptions in KV), `/sync-holdings` (receives the compact holdings snapshot), a `scheduled()` cron handler that compares live prices to your holdings and fires alerts for any move ≥3%, with rupee value and % of total portfolio, deduped to once per symbol per day.
- `index.html` — a throttled effect (once per 6h) that posts `{sym, qty}` + total portfolio value to `/sync-holdings`.

## Steps to actually turn this on

1. **Find your existing VAPID private key.** The public key `BC63wRMuF6n8...` is already embedded in the live site, which means a private key was generated to match it at some point. If you (or whoever set this up) still have it saved, use it below. **If it's lost, we have to generate a new pair and I'll need to update the public key in `index.html` too** — tell me and I'll do that instead.

2. **Install the push-sending dependency** (the Worker now imports `web-push`, which needs Node compat mode):
   ```bash
   npm install web-push
   ```
   In `wrangler.toml`, add:
   ```toml
   compatibility_flags = ["nodejs_compat"]
   ```
   (alongside whatever `compatibility_date` you already have).

3. **Set the two new secrets** (never put these in the file itself):
   ```bash
   wrangler secret put VAPID_PRIVATE_KEY
   wrangler secret put VAPID_SUBJECT   # e.g. mailto:jashshah379@gmail.com — optional, defaults to that if unset
   ```
   `VAPID_PUBLIC_KEY` should already be set the same way it was when the subscribe flow was first built — if unsure, check `wrangler secret list` or your dashboard's Worker → Settings → Variables.

4. **Add the Cron Trigger.** In `wrangler.toml`:
   ```toml
   [triggers]
   crons = ["*/5 4-9 * * 1-5"]
   ```
   That's every 5 minutes, 4:00–10:00 UTC, Mon–Fri — covers NSE's 9:15–15:30 IST window (IST = UTC+5:30) with a little buffer. Adjust the `*/5` if you want it more/less frequent — more frequent doesn't create duplicate alerts (the dedupe key stops that), it just detects a move sooner.

5. **Deploy:**
   ```bash
   wrangler deploy
   ```

6. **Redeploy the dashboard** with the updated `index.html` (same process as always — swap it in, push to the repo).

7. **Test on your phone.** Open the app, grant notification permission if you haven't (this is the existing `enableNotifications()` flow — check wherever that button/toggle lives in the app already). Then:
   - Confirm a subscription landed: `curl https://noisy-sea-5936.jashshah379.workers.dev/prices` still works as a basic Worker-is-alive check, but to see subscriptions you'd need a small KV list — ask me and I'll add a debug route if useful.
   - Force a holdings sync immediately rather than waiting 6h: in the browser console, run `localStorage.removeItem('shah_holdings_sync_v1')` then reload.
   - To verify the alert logic itself without waiting for a real 3% move, temporarily lower `MOVE_ALERT_THRESHOLD_PCT` in `worker.js` to something you know will trigger (e.g. `0.1`), deploy, wait for the next cron tick, confirm the notification arrives, then set it back to `3` and redeploy.

## Honest caveats

- **I can't test any of this end-to-end from here** — no real device, no access to Apple's/Google's push services from this sandbox. Steps 6–7 are on you.
- **Value/portfolio-% numbers are approximate.** `dayChangeValue` uses Yahoo's `regularMarketChange × your qty` — accurate for straightforward long positions, less precise for MTF/leveraged positions where your actual capital at risk differs from the raw share value.
- **The holdings snapshot is family-wide** (all `ALL_FAMILY` holdings, not just your personal accounts) since that's what "my portfolio" maps to in the existing app's data model. If you actually want this scoped to just your own accounts, say so and I'll change what gets synced.
