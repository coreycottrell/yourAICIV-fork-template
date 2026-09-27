---
name: partner-notifications
description: "OFF BY DEFAULT: reseller notifications come from True Bearing, not from you. config/partner.json ships with an empty notify_emails, so you never email the reseller, nothing is queued, and there is no email status to report. This skill documents the dormant AiCIV-side feed an operator can switch on for one civ (one email per event: born, first conversation, WOW shipped, trial milestones, health, business alerts). Load only when an operator asks about or switches on partner notifications."
version: 1.1.0
status: provisional
authored: 2026-09-27
authored_by: True Bearing dev VP (yourAICIV WS8)
applicable_agents: [primary, comms-vp, dev-vp]
sender: tools/partner_notify.py          # thin: compose, dedupe, queue, send
recipients: config/partner.json notify_emails (override: PARTNER_NOTIFY_EMAILS); EMPTY by default = off
state: memories/partner-notifications/  # keys/ (sent once), outbox/ (waiting), sent/, status.json
sibling_skills:
  - agentmail-mastery (the email capability the sender uses)
  - first-visit-evolution / identity-interview (first conversation)
  - three-wow-builds-protocol / m3-trial-mode (WOW builds, trial)
  - client-onboarding (the delivery engine whose alerts are copied)
---

# Partner notifications

## 0. Off by default (Corey 2026-09-27)

**Reseller notifications come from True Bearing, not from you.** Not every AiCIV has an email
inbox, and True Bearing already emails the reseller about billing, trial and conversion events
from its own side. So `config/partner.json` ships with `"notify_emails": []`, and while it is
empty:

- you do **not** email the reseller, and no skill asks you to;
- `tools/partner_notify.py` does nothing at all: no email, no outbox, no
  `memories/partner-notifications/` directory, no health probe;
- there is **no** "email not provisioned / queued / can't send" status. Never tell your human
  or operator that you cannot email the partner: it is not something you are meant to do;
- client-site business alerts go to the client owner only.

`python3 tools/partner_notify.py enabled` exits 1 while it is off. Everything below describes the
dormant feed, for an operator who switches it on for one civ by putting addresses in
`notify_emails` or setting `PARTNER_NOTIFY_EMAILS`. That civ then needs an AgentMail inbox.

## What the feed does when switched on

The reseller partner's client is your human. The partner cannot see inside your container, so
the feed tells them, by email, when something that matters happens. The human never sees these
emails. It is a courtesy feed, not a report card: short, plain, factual.

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

It prints one line: `SENT`, `QUEUED (why)`, `ALREADY REPORTED`, or `OFF` (the default: nothing sent). It never fails
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

## 4. Switched on but email is not set up yet

This applies only when the feed is switched on. If your AgentMail inbox is not provisioned, every notice is **queued** in
`memories/partner-notifications/outbox/` and your session start shows:
`[Partner notifications] N waiting ... no email capability is provisioned yet`. Say so plainly if
asked about your status. They are sent automatically (watchdog, every minute) the moment an
AgentMail key exists (`civ/config/agentmail.env` or `AGENTMAIL_API_KEY`; see agentmail-mastery).
Check any time: `python3 tools/partner_notify.py status`.

## 5. Delivery-engine alerts

Every client site you run (`apps/<slug>/`, skill client-onboarding) sends the owner a Telegram
alert for a new lead, order, booking, or affiliate application. By default that is all: owner
only. When switched on, the same alert is also emailed to the partner through the site's email
provider (Resend). If the site has no email provider yet, or the
send fails, the alert is queued to `apps/<slug>/logs/partner-outbox.jsonl` and the watchdog sends
it from your own inbox. Nothing to do by hand. A site's partner list comes from
`config/partner.json`; `PARTNER_NOTIFY_EMAILS` in the site's `.env` overrides it.

## 6. Anti-patterns

- Switching the feed on yourself, or emailing the reseller by hand. Off is the default; True
  Bearing handles reseller notifications.
- Telling anyone you "can't email the partner yet" while the feed is off.
- Asking the human whether to tell the partner. When switched on, routine notices are part of the service.
- Writing a report instead of a notice. Three lines is plenty.
- Sending test or demo emails to the partner. Test against your own inbox
  (`PARTNER_NOTIFY_EMAILS=<your inbox> python3 tools/partner_notify.py send ...`).
- Editing `config/partner.json` to change recipients. That is the operator's file.

## 7. Firing contract

Fired = an entry in `memories/partner-notifications/keys/` for the event AND either a file in
`sent/` or a file in `outbox/` with `last_error` explaining why it waits. Status:
`python3 tools/partner_notify.py status --json`.
