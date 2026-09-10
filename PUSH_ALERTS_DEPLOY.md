# Push move-alerts — corrected deploy checklist

(Supersedes the earlier version of this file — that one was built against a stale
copy of worker.js and got the KV namespace name and push implementation wrong.
This one is built against the actual file you pasted.)

## What was already live before this session
- VAPID public key embedded client-side, subscribe flow, `sw.js` push/notificationclick handlers
- A KV namespace bound as `PUSH_SUBS` for subscriptions
- A KV namespace bound as `SHAH_KV` for holdings/bank admin data + price cache
- A **self-contained, zero-dependency** Web Push implementation (`sendWebPush`, `generateVapidJWT`, `encryptWebPushPayload`) using only `crypto.subtle` — no npm, no build step, deploys the same way this file always has
- `/push-subscribe`, `/push-unsubscribe`, `/push-test` routes

## What this drop adds
- `MOVE_ALERT_THRESHOLD_PCT` / `PORTFOLIO_SIGNIFICANT_PCT` / `ALERT_DEDUPE_TTL` config + `checkMoveAlerts(env)` — compares your synced holdings against `fetchAll(env)`'s live prices, computes rupee value and % of total portfolio for anything moving ≥3%, sends via the existing `sendWebPush`, deduped per symbol per day
- `scheduled(event, env, ctx)` export — runs `checkMoveAlerts` on a Cron Trigger
- `POST /sync-holdings` — stores the `{sym, qty}[]` + `totalValue` snapshot the dashboard now posts periodically (client-side change from earlier in this conversation is compatible as-is — same request shape)

## Steps to turn it on

1. **Confirm your VAPID secrets are already set.** Since `/push-test` already existed and depends on `env.VAPID_PUBLIC_KEY` / `env.VAPID_PRIVATE_KEY`, they should already be configured. Sanity check: hit `/push-test` after you've enabled notifications once in the app — if it doesn't error on missing keys, you're set. Nothing new to do here.

2. **Add a Cron Trigger** (this is the one genuinely new piece of Cloudflare config). In your `wrangler.toml`:
   ```toml
   [triggers]
   crons = ["*/5 4-9 * * 1-5"]
   ```
   Every 5 minutes, 4:00–10:00 UTC, Mon–Fri — covers NSE's 9:15–15:30 IST with a little buffer (IST = UTC+5:30). If you deploy via the Cloudflare dashboard instead of wrangler, add the same schedule under **Workers & Pages → this worker → Triggers → Cron Triggers**.

3. **Deploy `worker.js`** the same way you always do (dashboard paste or `wrangler deploy` — no new dependencies, no `nodejs_compat` flag needed, still a single file).

4. **Redeploy `index.html`** with the holdings-sync effect from earlier in this conversation, if you haven't already.

5. **Test without waiting for a real 3% move:** temporarily set `MOVE_ALERT_THRESHOLD_PCT` to something trivial like `0.1`, deploy, wait for the next cron tick (or manually trigger it if your Cloudflare plan supports "Trigger Event" in the dashboard), confirm a push lands, then set it back to `3`.

## Caveats (unchanged from before)
- Can't test actual push delivery from this sandbox — no real device, no access to Apple's/Google's push services here.
- `dayChangeValue` uses Yahoo's `regularMarketChange × qty` — accurate for plain long positions, approximate for MTF/leveraged ones.
- Holdings snapshot is family-wide (`ALL_FAMILY`), not scoped to just your personal accounts, unless you tell me to narrow it.
