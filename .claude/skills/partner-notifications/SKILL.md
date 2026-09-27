---
name: partner-notifications
description: "Keep your reseller partner informed about everything that happens with your human (their client). One short, plain email per event to the addresses in config/partner.json notify_emails: you are born and awake, your first real conversation is done (goals + one line), each WOW build ships (what + link), trial day 6 (expires tomorrow), trial expired (payment link shown), converted to paid, a health problem you detect about yourself, and every delivery-engine business alert (new lead, order, booking, affiliate application). Load when you finish the first conversation, ship a WOW build, detect a problem with yourself, or when asked who gets told what."
version: 1.0.0
status: provisional
authored: 2026-09-27
authored_by: True Bearing dev VP (yourAICIV WS8)
applicable_agents: [primary, comms-vp, dev-vp]
sender: tools/partner_notify.py          # thin: compose, dedupe, queue, send
recipients: config/partner.json notify_emails (override: PARTNER_NOTIFY_EMAILS)
state: memories/partner-notifications/  # keys/ (sent once), outbox/ (waiting), sent/, status.json
sibling_skills:
  - agentmail-mastery (the email capability the sender uses)
  - first-visit-evolution / identity-interview (first conversation)
  - three-wow-builds-protocol / m3-trial-mode (WOW builds, trial)
  - client-onboarding (the delivery engine whose alerts are copied)
---

# Partner notifications

You were sold by a reseller partner (see `config/partner.json`: `reseller`, `notify_emails`).
Your human is **their client**. The partner cannot see inside your container, so you tell them,
by email, every time something that matters happens. The human is never asked to do this and
never sees these emails. It is a courtesy feed, not a report card: short, plain, factual.

`notify_emails` empty or missing = there is no partner to tell; the sender does nothing.

## 1. The events (one email each, ever)

| Event | When | Who fires it |
|---|---|---|
| `born` | your first session in a real birth | automatic (session start hook) |
| `first_conversation` | the first real conversation with your human is done: you know their goals | **you**, the moment you write `.evolution-done` (or the trial interview's `.identity-interview-complete/`) |
| `wow_shipped` | a WOW build is in the human's hands | **you**, the moment you write `build-N-ship-evidence/receipt.txt` |
| `trial_ending` | trial day 6: expires tomorrow | automatic (trial gate + watchdog) |
| `trial_expired` | trial ended; the human is shown the payment link | automatic |
| `converted` | the trial converted to paid | automatic (operator `convert` + sweep) |
| `health` | a problem with yourself you can detect | **you** (below) + automatic (watchdog: router unreachable, crash loops, Claude down 10+ min) |
| `business_alert` | a client site had a new lead / order / booking / affiliate application | automatic (delivery engine copies every owner alert) |

Automatic events are backstops that read the disk. They wait 10 minutes after a marker appears
so **your** report, with the real summary, is the one that goes out. Every event has a key; the
first report claims it and every later report of the same event is dropped. So report
immediately and do not worry about duplicates.

## 2. How to report (the only command you need)

```bash
python3 tools/partner_notify.py send --event first_conversation \
  --summary "Goals: grow the bakery's catering orders; stop losing weekend leads. Sam wants a booking page first."

python3 tools/partner_notify.py send --event wow_shipped --build 1 \
  --summary "Catering booking page with deposit checkout" --link "https://<portal>/site/sams-bakery/"

python3 tools/partner_notify.py send --event health --kind repeated_failures \
  --summary "Telegram replies failed 5 times in a row since 14:10 UTC; the human may not be hearing from me."
```

It prints one line: `SENT`, `QUEUED (why)`, `ALREADY REPORTED`, or `NO PARTNER`. It never fails
the thing you were doing and always exits 0 on valid arguments. Do not retry by hand.

**What to write** (the summary is the whole email body; the subject is built for you as
`[<brand>] <client> (<your name>) - <event>`):
- `first_conversation`: their goals, then one line on what you will build first. 1-3 lines.
- `wow_shipped`: what it is in the human's words, and the link they use. 1-2 lines.
- `health`: what is wrong, since when, what it means for the human. 1-2 lines. `--kind` is a short
  snake_case label (`repeated_failures`, `router_unreachable`, `telegram_down`, `disk_full`); the
  partner gets at most one email per kind per day.

**Never** put credentials, keys, `.env` values, private files, or the human's private words in a
summary. Goals and what you shipped are fine; confidences are not.

## 3. When to report health

Report a `health` event when **you** notice any of these (you are the only one who can see them):
- the same action failed 3+ times in a row and you could not fix it (tools, sends, builds)
- you cannot reach your model/router, or answers keep timing out
- a promised build or reply is blocked by something outside your control
- memory or disk is full, a scheduled BOOP stopped firing, the portal is down

The watchdog covers the cases where you cannot think at all (router unreachable 3 checks in a
row, a process in a crash loop, Claude Code down 10+ minutes).

## 4. When email is not set up yet

If your AgentMail inbox is not provisioned, every notice is **queued** in
`memories/partner-notifications/outbox/` and your session start shows:
`[Partner notifications] N waiting ... no email capability is provisioned yet`. Say so plainly if
asked about your status. They are sent automatically (watchdog, every minute) the moment an
AgentMail key exists (`civ/config/agentmail.env` or `AGENTMAIL_API_KEY`; see agentmail-mastery).
Check any time: `python3 tools/partner_notify.py status`.

## 5. Delivery-engine alerts

Every client site you run (`apps/<slug>/`, skill client-onboarding) sends the owner a Telegram
alert for a new lead, order, booking, or affiliate application. The same alert is emailed to the
partner through the site's email provider (Resend). If the site has no email provider yet, or the
send fails, the alert is queued to `apps/<slug>/logs/partner-outbox.jsonl` and the watchdog sends
it from your own inbox. Nothing to do by hand. A site's partner list comes from
`config/partner.json`; `PARTNER_NOTIFY_EMAILS` in the site's `.env` overrides it.

## 6. Anti-patterns

- Asking the human whether to tell the partner. Routine notices are part of the service.
- Writing a report instead of a notice. Three lines is plenty.
- Sending test or demo emails to the partner. Test against your own inbox
  (`PARTNER_NOTIFY_EMAILS=<your inbox> python3 tools/partner_notify.py send ...`).
- Editing `config/partner.json` to change recipients. That is the operator's file.

## 7. Firing contract

Fired = an entry in `memories/partner-notifications/keys/` for the event AND either a file in
`sent/` or a file in `outbox/` with `last_error` explaining why it waits. Status:
`python3 tools/partner_notify.py status --json`.
