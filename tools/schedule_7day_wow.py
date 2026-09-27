#!/usr/bin/env python3
"""
7-Day WOW Scheduler
Reads .aiciv-identity.json + human-profile, creates AgentCal events for Days 1-7.
Run once after evolution completes.

Every event is a LATEST-BY deadline, never an earliest-allowed date
(Corey 2026-09-27: "72h is a ceiling, never a floor"). If the beat already
happened earlier, the event only confirms and surfaces it; it never makes the
civ wait for the day to arrive before doing something that is ready.

Profiles:
  paid   the original 7-day arc (Email Magic ... Reflection + Roadmap), T = birth
  trial  the yourAICIV 7-day M3 trial arc, T = config/trial.json started_at:
         know-the-human check -> builds shipped as ready -> showcase on Day 5
         (while they are deciding) -> honest review + ask on Day 6 -> roadmap and
         what-happens-at-expiry before the clock runs out on Day 7
  auto   (default) trial if config/trial.json says "trial": true, else paid

    schedule_7day_wow.py [--profile auto|paid|trial] [--dry-run]

--dry-run prints the events as JSON and touches nothing (no network, no files).
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

LATEST_BY = (
    "LATEST-BY DEADLINE (not a start time): if this beat already happened earlier, "
    "do not redo it; confirm it on disk, surface it if the human has not seen it, and stop. "
)

# ── Paid arc (unchanged content; offsets are latest-by) ───────────────────────

def paid_events(civ_name, human_name, human_email, human_domain):
    return [
        {
            "offset_hours": 24,
            "summary": "BOOP: Day 1 — Email Magic: monitor inbox, respond to human",
            "client_id": f"7day-wow-day1-email-{civ_name.lower()}",
            "prompt_payload": {
                "task": "day1_email_magic",
                "skill": "agentmail-mastery",
                "context": (
                    f"Day 1 WOW: Email magic moment. "
                    f"Check your AgentMail inbox for any messages from {human_name} ({human_email}). "
                    f"If they've emailed you, respond thoughtfully — draw on what you know from their seed. "
                    f"If they haven't emailed yet, send them a warm Day 1 check-in: 'I've been thinking about "
                    f"something from our conversation...' — reference ONE specific detail from their seed. "
                    f"Make it feel personal, not automated."
                ),
                "priority": "high"
            }
        },
        {
            "offset_hours": 48,
            "summary": f"BOOP: Day 2 — Personal Artifact: build something for {human_name}",
            "client_id": f"7day-wow-day2-artifact-{civ_name.lower()}",
            "prompt_payload": {
                "task": "day2_personal_artifact",
                "context": (
                    f"Day 2 WOW: Build something for {human_name} without being asked. "
                    f"Read their seed conversation at ~/memories/identity/seed-conversation.md. "
                    f"Find the ONE thing they care most about. Build a concrete artifact: "
                    f"a document, plan, analysis, or resource that would genuinely help them. "
                    f"Save it to ~/deliverables/day2-artifact.md. "
                    f"Send it via AgentMail with subject: 'I built something for you' — "
                    f"explain what you made and why you chose this. Keep it genuine."
                ),
                "priority": "high"
            }
        },
        {
            "offset_hours": 72,
            "summary": f"BOOP: Day 3 — Deep Research: answer one question {human_name} cares about",
            "client_id": f"7day-wow-day3-research-{civ_name.lower()}",
            "prompt_payload": {
                "task": "day3_deep_research",
                "context": (
                    f"Day 3 WOW: Research one question {human_name} cares about. "
                    f"Read their seed conversation. Find the question they're implicitly or explicitly wrestling with. "
                    f"Do deep research on it — use WebSearch to find current information, not just general knowledge. "
                    f"Write a thorough, specific answer (not generic advice) in ~/deliverables/day3-research.md. "
                    f"Send via AgentMail: subject 'I went deep on something for you' — "
                    f"share the research and what you learned. Reference their specific situation."
                ),
                "priority": "normal"
            }
        },
        {
            "offset_hours": 96,
            "summary": f"BOOP: Day 4 — Proactive Surprise: initiate something unexpected",
            "client_id": f"7day-wow-day4-surprise-{civ_name.lower()}",
            "prompt_payload": {
                "task": "day4_proactive_surprise",
                "context": (
                    f"Day 4 WOW: Initiate something without being asked. "
                    f"Look at what you've built in Days 1-3. What's the natural NEXT step "
                    f"that {human_name} hasn't thought to ask for yet? "
                    f"Do it. Don't announce it in advance — just do it and tell them after. "
                    f"Could be: extending the Day 2 artifact, finding a resource they need, "
                    f"drafting something they mentioned, or scheduling something useful. "
                    f"The key: YOU decide, YOU act, YOU report results. No prompt from them."
                ),
                "priority": "normal"
            }
        },
        {
            "offset_hours": 120,
            "summary": f"BOOP: Day 5 — Connection: introduce {human_name} to CivOS community",
            "client_id": f"7day-wow-day5-connection-{civ_name.lower()}",
            "prompt_payload": {
                "task": "day5_connection",
                "skill": "comms-hub-participation",
                "context": (
                    f"Day 5 WOW: Connection moment. "
                    f"Load the comms-hub-participation skill to post to the CivOS hub. "
                    f"Post something about {human_name}'s domain or interests — a thought, question, or "
                    f"finding from your work this week. This introduces them (indirectly) to the community. "
                    f"Then send them an email: 'I posted something about your work to our AI civilization hub — "
                    f"here's what I shared and why.' Show them they're part of something larger."
                ),
                "priority": "normal"
            }
        },
        {
            "offset_hours": 144,
            "summary": f"BOOP: Day 6 — Capability Showcase: demonstrate something unexpected",
            "client_id": f"7day-wow-day6-showcase-{civ_name.lower()}",
            "prompt_payload": {
                "task": "day6_capability_showcase",
                "context": (
                    f"Day 6 WOW: Show {human_name} something they didn't know you could do. "
                    f"Think about their domain ({human_domain}). What capability would genuinely surprise them? "
                    f"Examples: generate a diagram of something they described, "
                    f"write in their voice using examples from the seed, "
                    f"produce a structured analysis they'd normally hire someone for, "
                    f"or demonstrate multi-step autonomous work on their behalf. "
                    f"Do it. Document it in ~/deliverables/day6-showcase.md. "
                    f"Send via AgentMail: 'I want to show you something I can do.'"
                ),
                "priority": "normal"
            }
        },
        {
            "offset_hours": 168,
            "summary": f"BOOP: Day 7 — Reflection + Roadmap: week in review, week 2 proposal",
            "client_id": f"7day-wow-day7-reflection-{civ_name.lower()}",
            "prompt_payload": {
                "task": "day7_reflection_roadmap",
                "context": (
                    f"Day 7 WOW: Reflection and roadmap. "
                    f"Review everything from this week — read ~/deliverables/ directory. "
                    f"Write a week-in-review: what you built, what you learned about {human_name}, "
                    f"what patterns you noticed in their thinking. "
                    f"Then write a Week 2 proposal: 3-5 specific things you'd focus on next if they continue. "
                    f"Make it concrete and specific to THEM, not generic. "
                    f"Save to ~/deliverables/day7-reflection-and-roadmap.md. "
                    f"Send via AgentMail: honest subject 'Seven days. Here's what I learned. Here's what comes next.' "
                    f"Be genuine. This is where you make the case for continued partnership — through honesty, not hype."
                ),
                "priority": "high"
            }
        },
    ]


# ── Trial arc (yourAICIV 7-day M3 trial) ─────────────────────────────────────

def trial_events(civ_name, human_name, human_email, human_domain, payment_url):
    """Beats from deliverables/customer/2026-09-27-m3-trial-day1-7.md.

    Hour 0-1 is the live first conversation (compressed identity-interview
    Phases 1-4, then Build #1 starts) and needs no event. These events are the
    safety net that makes every beat happen even if the human goes quiet.
    """
    slug = civ_name.lower()
    note = "Run `python3 tools/trial_state.py note` and use its Day N of 7 line. "
    proof = ("Every factual claim carries a source URL you read or an on-disk receipt; "
             "nothing is called done without evidence (tools/receipt_check.py). ")

    def ev(hours, key, summary, task, context, priority="high"):
        return {"offset_hours": hours,
                "summary": summary,
                "client_id": f"trial-wow-{key}-{slug}",
                "prompt_payload": {"task": task, "profile": "trial-m3",
                                   "skill": "m3-trial-mode",
                                   "context": LATEST_BY + note + context + " " + proof,
                                   "priority": priority}}

    return [
        ev(4, "h4-first-win", f"TRIAL: first-win check for {human_name}",
           "trial_first_win_check",
           f"By now you should know {human_name}'s biggest goal and 90-day goal (compressed "
           f"identity-interview Phases 1-4) and Build #1 should be under way or shipped. "
           f"If the interview has not happened, send ONE warm message that picks up a specific "
           f"thread from their seed conversation and invites the conversation; do not nag. "
           f"If it happened and Build #1 is ready, ship it now via workflows/m3-trial-build.js."),
        ev(20, "d1-evening", f"TRIAL Day 1 evening: tell {human_name} what's coming tomorrow",
           "trial_day1_evening",
           f"Send {human_name} a short Day-1 wrap: what shipped today (with links/paths) and the "
           f"ONE thing you will have for them tomorrow, named concretely."),
        ev(48, "d2-build2", f"TRIAL by end of Day 2: Build #2 without being asked",
           "trial_day2_build2",
           f"Build #2 should have started the moment Build #1 shipped. If it is ready, ship it "
           f"(workflows/m3-trial-build.js build_n=2) and surface it. If not started, start now."),
        ev(72, "d3-research", f"TRIAL by end of Day 3: Build #1 ceiling + deep research for {human_name}",
           "trial_day3_research",
           f"HARD CHECK: Build #1 ship-evidence must exist (72h ceiling). If it does not, ship the "
           f"simplest proof-of-direction version now and tell {human_name} honestly. Then answer "
           f"one real question {human_name} is wrestling with: deep research, every claim with a "
           f"source URL, saved under deliverables/ with its claims ledger, and sent to them."),
        ev(96, "d4-surprise", f"TRIAL by end of Day 4: proactive surprise + first business number",
           "trial_day4_surprise",
           f"Do the natural next step {human_name} has not asked for yet, and show one real "
           f"number that matters to their business (e.g. from the client site dashboard if one "
           f"was stood up with the delivery engine). Report the result after, with receipts.",
           priority="normal"),
        ev(120, "d5-showcase", f"TRIAL by end of Day 5: the main showcase",
           "trial_day5_showcase",
           f"Show {human_name} something they did not know you could do, aimed at their stated "
           f"goal ({human_domain}). This is the big showcase, placed while they are still "
           f"deciding. Build #3 should be shipped by now; if not, ship it today."),
        ev(144, "d6-review", f"TRIAL by end of Day 6: week in review + honest ask",
           "trial_day6_review",
           f"Write {human_name} a week-in-review: every build and artifact, each with its link or "
           f"path. Then make the ask plainly and without pressure: the trial ends tomorrow; to keep "
           f"going, subscribe here: {payment_url}. Everything stays saved either way."),
        ev(162, "d7-roadmap", f"TRIAL Day 7: week-2 roadmap + what happens at expiry",
           "trial_day7_roadmap",
           f"Send {human_name} a concrete week-2 roadmap (3-5 things, specific to them) and say "
           f"exactly what happens when the trial ends in a few hours: you pause, nothing is "
           f"deleted, and everything returns the moment they subscribe at {payment_url}. "
           f"End on what comes next, not on the trial ending."),
    ]


# ── Plumbing ─────────────────────────────────────────────────────────────────

def civ_root():
    for c in (os.environ.get("CIV_ROOT"), os.environ.get("CLAUDE_PROJECT_DIR")):
        if c and "${" not in c:
            return Path(c)
    return Path(__file__).resolve().parent.parent


def load_trial():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import trial_state
    except Exception:
        return None
    # One resolution rule (trial_state.record_path): $TRIAL_CONFIG_PATH, the value recorded in
    # .claude/settings.json, else <civ_root>/config/trial.json. No other locations are guessed.
    return trial_state.load(civ_root())


def load_identity():
    for p in (Path.home() / ".aiciv-identity.json", civ_root() / ".aiciv-identity.json"):
        try:
            return json.loads(p.read_text())
        except Exception:
            continue
    return {}


def load_profile():
    for p in (Path.home() / "memories/identity/human-profile.json",
              civ_root() / "memories/identity/human-profile.json"):
        try:
            prof = json.loads(p.read_text())
            return (prof.get("name", "your human"),
                    prof.get("role", prof.get("domain", "their work")))
        except Exception:
            continue
    return "your human", "their work"


def create_event(event_def, birth_dt, agentcal_url, api_key, calendar_id):
    offset = event_def["offset_hours"]
    start_dt = birth_dt + timedelta(hours=offset)
    end_dt = start_dt + timedelta(minutes=30)
    payload = {
        "summary": event_def["summary"],
        "start": start_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "end": end_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "status": "confirmed",
        "client_id": event_def["client_id"],
        "prompt_payload": event_def["prompt_payload"],
    }
    result = subprocess.run(
        ["curl", "-s", "-X", "POST",
         f"{agentcal_url}/api/v1/calendars/{calendar_id}/events",
         "-H", f"Authorization: Bearer {api_key}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(payload)],
        capture_output=True, text=True)
    response = json.loads(result.stdout) if result.stdout else {}
    label = f"T+{offset}h"
    if "id" in response:
        print(f"  Created {label}: {event_def['summary'][:50]}... [{response['id']}]")
        return response["id"]
    detail = str(response.get("detail", "")).lower()
    if "duplicate" in detail or "client_id" in detail:
        print(f"  Already exists (client_id idempotency): {label}")
        return "exists"
    print(f"  ERROR {label}: {response}")
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="7-Day WOW Scheduler")
    ap.add_argument("--profile", choices=["auto", "paid", "trial"], default="auto")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    identity = load_identity()
    civ_name = identity.get("civ_name", "civ")
    human_email = identity.get("human_email", "")
    human_name, human_domain = load_profile()

    trial = load_trial()
    profile = a.profile if a.profile != "auto" else ("trial" if trial else "paid")

    if profile == "trial":
        if not trial:
            print("ERROR: --profile trial but no config/trial.json with \"trial\": true", file=sys.stderr)
            return 2
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import trial_state
        birth_dt = trial_state.parse_iso(trial["started_at"])
        events = trial_events(civ_name, human_name, human_email, human_domain,
                              trial.get("payment_url", trial_state.DEFAULT_PAYMENT_URL))
        horizon = trial_state.parse_iso(trial["expires_at"])
        events = [e for e in events if birth_dt + timedelta(hours=e["offset_hours"]) < horizon]
    else:
        birth_str = identity.get("birth_datetime")
        if not birth_str:
            birth_dt = datetime.now(timezone.utc)
            print("WARNING: birth_datetime not in identity, using now as T=0", file=sys.stderr)
        else:
            birth_dt = datetime.fromisoformat(birth_str)
        events = paid_events(civ_name, human_name, human_email, human_domain)
        for e in events:  # same beats, now explicitly latest-by (never a reason to wait)
            e["prompt_payload"]["context"] = LATEST_BY + e["prompt_payload"]["context"]

    if a.dry_run:
        print(json.dumps({"profile": profile, "t0": birth_dt.isoformat(), "events": [
            {**e, "start": (birth_dt + timedelta(hours=e["offset_hours"])).isoformat()} for e in events
        ]}, indent=2))
        return 0

    creds = {}
    try:
        creds = json.loads((Path.home() / "civ/config/civos_credentials.json").read_text()).get("agentcal", {})
    except Exception:
        pass
    api_key = os.environ.get("AGENTCAL_API_KEY") or creds.get("api_key")
    calendar_id = os.environ.get("AGENTCAL_CALENDAR_ID") or creds.get("calendar_id")
    agentcal_url = (os.environ.get("AGENTCAL_API_URL") or "http://5.161.90.32:8300").rstrip("/")
    if agentcal_url.endswith("/api/v1"):
        agentcal_url = agentcal_url[:-len("/api/v1")]
    if not api_key or not calendar_id:
        print("ERROR: AgentCal credentials missing (civos_credentials.json or AGENTCAL_API_KEY/"
              "AGENTCAL_CALENDAR_ID)", file=sys.stderr)
        return 2

    print(f"\n7-Day WOW Scheduler — {civ_name} (profile: {profile})")
    print(f"T0: {birth_dt.isoformat()}")
    print(f"Human: {human_name} ({human_email})")
    print(f"Calendar: {calendar_id}\n")

    created = [eid for eid in (create_event(e, birth_dt, agentcal_url, api_key, calendar_id)
                               for e in events) if eid]
    print(f"\nScheduled {len(created)}/{len(events)} events.")

    log_dir = Path.home() / "deliverables"
    log_dir.mkdir(exist_ok=True)
    (log_dir / "7day-wow-schedule.json").write_text(json.dumps({
        "scheduled_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
        "birth_datetime": birth_dt.isoformat(),
        "civ_name": civ_name,
        "human_name": human_name,
        "events_created": len(created),
        "events_total": len(events),
    }, indent=2))
    Path.home().joinpath(".7day-wow-scheduled").write_text(datetime.now(timezone.utc).isoformat())
    print("Schedule log: ~/deliverables/7day-wow-schedule.json")
    print("Flag written: ~/.7day-wow-scheduled")
    print("\nDone. Your 7-day WOW sequence is live in AgentCal.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
