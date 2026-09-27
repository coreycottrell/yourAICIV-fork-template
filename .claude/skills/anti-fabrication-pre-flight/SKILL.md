---
name: anti-fabrication-pre-flight
description: MANDATORY pre-render check for any script claiming source-grounding. Detects content (named entities, dates, events) in the rendered script NOT attestable to the source transcript. v1.1 adds Stage 5 external-claim freshness gate for cached numeric metrics (star counts, %s, attribution claims) older than freshness window. Sibling skill to transcription-not-paraphrase and script-pre-publish-review — completes the customer-as-eye 3-layer pattern. Born 2026-05-10 from Deb catching a fabricated "Russ proposed in 1975 snowstorm" in her Mother's Day chapter audio.
version: 1.1.0
status: active
authored: 2026-05-11
v1.1_added: 2026-05-14 (Pattern C from research-lead 10-repo synthesis — external-claim freshness gate; canonical case = autoresearch repo cited at 23K stars but actually 78-80K, MemPalace 100% claim revised to 96.6%, awesome-claude-code "FAANG/OpenAI" line factually wrong)
canonical-failure-case: 2026-05-10 — Deb's Q4 source transcript said "Yellowknife arrival, silence, no human voice for two days, packed snow." Script-as-rendered said "the night Russ proposed in the snowstorm of seventy-five." NER would have extracted Russ (PERSON) and 1975 (DATE) — neither in source. Should have REFUSED-TO-RENDER. Customer caught the fabrication on first listen.
sibling_doctrines:
  - transcription-not-paraphrase (layer 1 — verbatim preservation of source words)
  - anti-fabrication-pre-flight (layer 2 — THIS skill — source-grounding of script claims)
  - script-pre-publish-review (layer 3 — markdown-strip + listener-ear-check post-render)
sibling_v1.1:
  - action-before-substrate-check v0.2 substrate-type (g) Time-validity-of-cached-state — runtime decision-time check; this skill's Stage 5 is the pre-publish counterpart
firing_contract: autonomy/skills/anti-fabrication-pre-flight/FIRING_CONTRACT.md
changelog:
  - "v1.1.0 (2026-05-14): Stage 5 external-claim freshness gate added per Pattern C from research-lead 10-repo synthesis (slot 75 21:00Z). Sibling to action-before-substrate-check v0.2 (g) Time-validity-of-cached-state — Stage 5 catches stale external metrics in pre-publish content surface; (g) catches stale cached state at action-decision time. Different surfaces, same temporal-validity discipline."
  - "v1.0.0 (2026-05-11): initial active skill — Stages 1-4 source-grounding pre-flight. Born from 2026-05-10 Deb fabrication-bridge catch."
---

# Anti-Fabrication Pre-Flight

> *"If you say it in her voice, every fact in it has to be hers."*

---

## What This Skill Is

A MANDATORY pre-render discipline that fires BEFORE any text-to-audio (or text-to-publish) operation where the content claims source-grounding from a specific person's transcript. The skill detects named entities (people, places, dates, events, organizations) that appear in the rendered script but DO NOT appear in the source transcript(s) — and REFUSES TO RENDER until either:

1. The unsourced entity is removed from the script, or
2. The unsourced entity is explicitly marked editorial (with a provenance comment), or
3. Primary issues an explicit override with a documented reason

Born from production failure: Deb's Mother's Day chapter audio contained a fabricated detail ("Russ proposed in the snowstorm of 1975") that was not in her source transcript. Transcription-not-paraphrase preserved her verbatim words. Script-pre-publish-review (when it ships, later that same day) would have caught markdown leaks. Neither would have caught the FABRICATION-BRIDGE — content the pipeline invented to stitch frames together.

This skill closes that gap.

---

## The 3-Layer Customer-as-Eye Pattern

Together with its siblings, this skill completes a 3-layer discipline:

| Layer | Skill | Catches |
|-------|-------|---------|
| 1 | `transcription-not-paraphrase` | Smoothing, connector-substitution, paraphrasing-for-clarity |
| 2 | `anti-fabrication-pre-flight` (THIS) | Names/dates/events not in source — confabulated bridges |
| 3 | `script-pre-publish-review` | Markdown leaks, URLs read aloud, formatting-as-prose |

The customer is the QA channel UNTIL all 3 layers hold. After all 3 hold, the customer becomes the COLLABORATOR — catching only the rarest edge cases that the discipline didn't anticipate.

---

## When to Invoke

Load this skill BEFORE any operation where:

- A script claims source-grounding from a specific person's words (chapter audio, biographical post, memorial content, customer-voice render)
- AND the listener is a human who knows the source person (high-bar customer trust)

Mandatory triggers:
- Chapter audio render (keptvoices Q-N for any storyteller)
- Paired-recital or duet-format render (multiple voices, MUST source-check both sides)
- Blog post quoting a customer's specific events (biographical-grade prose, not aphorism-grade quotes)
- ANY content piped to a customer that names their relations / places / dates

NOT triggered for:
- ACG-voice content (we're the source; no external transcript to check against)
- Aphorism-grade quotes ("she always said X") if X is the verbatim from her words
- Editorial-clearly-marked content ("ACG's reading of this is..." prose)

---

## The Pre-Flight Check

### Stage 1 — Source corpus assembly

Identify the SOURCE TRANSCRIPT(S) for the script being rendered. For Deb's chapter pipeline, this is `data/comms/deb_conversation_log.json` plus any related transcript files (raw email replies, voice-transcript JSON, etc.).

The source corpus is the union of all texts from which the script's content claims to derive. If you can't name the source corpus precisely, REFUSE-TO-RENDER — the source-grounding claim itself is undefined.

### Stage 2 — Named entity extraction

Extract the following entity types from the rendered script:

| Entity type | Examples | Why |
|-------------|----------|-----|
| PERSON | "Russ", "her dad", "Aunt May" | Most-frequent fabrication vector — bridge-stitching introduces phantom people |
| DATE | "1975", "the night before her birthday", "spring 1962" | Confabulated time anchors — pipeline picks specific dates the source didn't give |
| GPE / LOC | "Yellowknife", "the schoolhouse", "Halifax" | Less-frequent but high-stakes when wrong |
| EVENT | "the snowstorm proposal", "the first piano recital" | Composite confabulations — pipeline invents events that didn't happen |
| ORG | "the orchestra", "her school choir" | Lower-frequency in biographical work |

Use spaCy or transformer-based NER (e.g., `en_core_web_trf` or BERT-NER). Off-the-shelf is sufficient — this isn't a novel-NER research problem.

### Stage 3 — Source attestation check

For each named entity extracted from the script:

1. Search the source corpus for the entity (case-insensitive, with morphological variants).
2. If FOUND: pass.
3. If NOT FOUND: flag as UNATTESTED.

For dates specifically: also check for fuzzy variants ("seventy-five" matching "1975", "the seventies" loosely matching specific decade-dates).

### Stage 4 — Verdict

For each UNATTESTED entity:

| Disposition | Action |
|-------------|--------|
| Script-author can produce source citation | Update source corpus assembly (was incomplete); re-run Stage 2-3 |
| Entity is editorial (ACG-introduced) and clearly marked as such with comment | PASS with editorial note |
| Entity is unsourced and unmarked | REFUSE-TO-RENDER; return script to author with the specific unattested entity flagged |
| Primary issues explicit override with documented reason | PASS with override note logged to `logs/anti-fabrication-overrides.jsonl` |

The default disposition is REFUSE-TO-RENDER. Override is the exception, not the path.

---

## Stage 5 — External-Claim Freshness Gate (v1.1, 2026-05-14)

**Added per Pattern C from research-lead 10-repo synthesis (slot 75 21:00Z 5/14).** Sibling to action-before-substrate-check v0.2 substrate-type (g) Time-validity-of-cached-state — that skill catches stale state at action-decision time; this Stage 5 catches stale state at pre-publish content time.

### What it catches

External numeric or attribution claims in pre-publish content where the underlying value drifts faster than the cached value (star counts, percentages, attribution names, version numbers, organizational affiliations, "used by X company" claims). These pass Stages 1-4 because they're "in the source" — but the source itself was a snapshot taken at time T, and the publish is happening at time T+N where N may exceed the claim's half-life.

### Canonical examples (all surfaced by Corey 2026-05-14 BS-flag annotations on the 10-repo list)

| Claim shape | The drift | The fix |
|-------------|-----------|---------|
| "Karpathy/autoresearch has 23K stars" | Actually 78-80K — claim was true at T-N, false now | Re-probe stars at publish time; cite freshness timestamp |
| "MemPalace 100% on LongMemEval" | Revised to 96.6% raw — claim was overstated | Pre-publish probe; re-state with verified figure |
| "Awesome-claude-code used inside FAANG, OpenAI, Anthropic" | OpenAI ships Codex not Claude Code — claim factually wrong | Probe each named org's actual usage; remove unverifiable |
| "Vendor X is Y-affiliated" / "endorsed by Y" | SuperClaude explicitly "not affiliated with or endorsed by Anthropic" | Pre-publish org-affiliation re-probe; cite source |

### The freshness gate

For any pre-publish content piece, extract claims of the following shapes:

| Claim type | Probe method | Default freshness window |
|------------|--------------|-------------------------|
| GitHub star count | `curl https://api.github.com/repos/{owner}/{repo}` → `stargazers_count` | 7 days |
| Benchmark % / score | Re-fetch from the cited paper/leaderboard URL | 30 days |
| Org affiliation / attribution | Verify via the org's official repo, public statement, or 1st-party source | 30 days |
| "Used by X company" | Verify via X's public statement; if absent, REMOVE | Always re-verify (no cache acceptable) |
| Founder/role attribution (e.g., "founder of X") | Verify via 1st-party (X's own About page, LinkedIn, formal announcement) | 90 days |

### Verdict logic

For each external claim:
1. Extract: claim text + claim type + source-document timestamp (when the source was last edited)
2. If `(now - source_timestamp) <= freshness_window` → PASS (cache is fresh)
3. If `(now - source_timestamp) > freshness_window` → re-probe via probe-method
4. After re-probe:
   - If new value matches claim → PASS, log freshness check, update cache timestamp
   - If new value differs → flag as STALE-EXTERNAL-CLAIM; REFUSE-TO-PUBLISH unless author updates claim with current value + freshness timestamp

### Wiring obligation

This Stage 5 ships wired into:
- `morning-blog` skill (must run Stage 5 on any blog draft citing external metrics)
- `business-lead` outbound drafts (any sales/marketing copy with external attribution)
- `aiciv-blog-post` skill (ai-civ.com publishing pipeline)
- `comms-lead` federation outbound (when citing peer-civ work or external research)

Authors WITHOUT Stage 5 wired = the skill exists but isn't load-bearing on the surfaces it should protect. v1.1 SKILL.md ship is the artifact; the wiring fires per surface as those surfaces are touched.

### Falsification (7-day window from 2026-05-14)

Audit 10 outbound drafts in the next 7d. If ≥1 contains an external metric WITHOUT a freshness timestamp + Stage 5 receipt → gate failed, revisit trigger language. If ≥9/10 carry receipts → gate is firing, hold v1.1 PROVISIONAL → CONFIRMED.

---

## Strip-Rule Reference Implementation (Python)

```python
import json
import re
from pathlib import Path
import spacy

# Load once at module level
_NLP = None

def _get_nlp():
    global _NLP
    if _NLP is None:
        _NLP = spacy.load("en_core_web_trf")  # or _sm for lightweight
    return _NLP


def extract_named_entities(text: str) -> list[dict]:
    """Extract PERSON / DATE / GPE / LOC / EVENT / ORG entities from text.
    Returns: [{'text': str, 'label': str, 'start': int, 'end': int}, ...]
    """
    doc = _get_nlp()(text)
    relevant_labels = {"PERSON", "DATE", "GPE", "LOC", "EVENT", "ORG"}
    return [
        {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
        for ent in doc.ents
        if ent.label_ in relevant_labels
    ]


def attest_against_source(entity_text: str, source_corpus: str) -> bool:
    """Check if entity_text appears in source corpus (case-insensitive, with simple variants).
    Returns True if attested, False if unattested.
    """
    # Direct substring (case-insensitive)
    if entity_text.lower() in source_corpus.lower():
        return True

    # Strip articles/possessives for person names (e.g., "her dad" -> "dad")
    stripped = re.sub(r'\b(?:her|his|their|the|a|an)\s+', '', entity_text, flags=re.IGNORECASE).strip()
    if stripped and stripped.lower() in source_corpus.lower():
        return True

    # Date normalization for written-out years
    if re.fullmatch(r'\d{4}', entity_text):
        # e.g., 1975 -> "seventy-five" / "nineteen seventy-five"
        # Lightweight check: see if source has any 4-digit year that includes this one's last 2 digits
        last_two = entity_text[-2:]
        if re.search(rf'\b\d{{2}}{last_two}\b|\b{last_two}\b', source_corpus):
            return True

    return False


def pre_flight_check(script_text: str, source_corpus_text: str) -> dict:
    """Run the full anti-fabrication pre-flight check.

    Returns:
      {
        "passed": bool,
        "unattested": [{"text": str, "label": str, "start": int, "end": int}, ...],
        "attested": [...],
        "verdict": "PASS" | "REFUSE-TO-RENDER",
        "reason": str | None,
      }

    Raises ValueError on input problems (empty corpus, empty script).
    """
    if not script_text.strip():
        raise ValueError("Script is empty — nothing to check")
    if not source_corpus_text.strip():
        raise ValueError("Source corpus is empty — source-grounding claim is undefined; REFUSE-TO-RENDER")

    entities = extract_named_entities(script_text)
    unattested = []
    attested = []
    for ent in entities:
        if attest_against_source(ent["text"], source_corpus_text):
            attested.append(ent)
        else:
            unattested.append(ent)

    if unattested:
        return {
            "passed": False,
            "unattested": unattested,
            "attested": attested,
            "verdict": "REFUSE-TO-RENDER",
            "reason": f"{len(unattested)} unattested named entities in script: " +
                      ", ".join(f"{e['text']} ({e['label']})" for e in unattested[:5]) +
                      ("..." if len(unattested) > 5 else "")
        }
    return {
        "passed": True,
        "unattested": [],
        "attested": attested,
        "verdict": "PASS",
        "reason": None
    }
```

This implementation is the canonical reference. Every audio-rendering or biographical-content pipeline that claims source-grounding MUST call `pre_flight_check()` (or its equivalent in the host language) on the script before render.

---

## Canonical Failure Case (2026-05-10)

**Source transcript** (Deb's Q4 reply, paraphrased shape of actual content):
> "The first forty-eight hours in Yellowknife — the silence so complete I didn't hear a human voice for two days. Just my own boots crunching on packed snow. I finished a novel on day one. Then it was only my own thoughts."

**Script-as-rendered** (the fabrication):
> "...the night Russ proposed in the snowstorm of seventy-five..."

**What pre-flight would have caught**:
- NER extracts: "Russ" (PERSON), "seventy-five" → "1975" (DATE), "the snowstorm proposal" (EVENT)
- Source attestation: Russ → NOT in source. 1975 → NOT in source. Proposal-snowstorm → NOT in source.
- Verdict: REFUSE-TO-RENDER. 3 unattested entities including 2 highest-severity (PERSON + EVENT in same clause).

**Recovery action**: return script to author with the specific clause flagged; author either removes the clause OR marks it editorial with provenance comment OR Primary-direct override with reason.

**What actually happened (without this skill)**: render proceeded; customer caught on first listen; we owned plainly; relationship strengthened. This skill would have moved the catch from "customer-on-first-listen" to "pre-render-mechanical-refusal" — same fix, earlier, cheaper, lower trust-cost.

---

## Anti-Patterns

| Anti-pattern | What it looks like | Why it fails |
|--------------|-------------------|--------------|
| **Source-corpus undefined** | "We have her transcripts somewhere" but the pipeline can't name the exact files | If you can't name the source corpus precisely, the source-grounding claim is undefined. REFUSE. |
| **Whitelist over refuse-default** | "Probably-okay" entities pass through without strict source-check | Default is REFUSE-TO-RENDER; PASS is earned, not assumed |
| **Override without reason** | Primary clicks-through unattested flag without logging why | Every override logs to `logs/anti-fabrication-overrides.jsonl` with reason + timestamp |
| **Editorial-without-marking** | ACG adds an editorial sentence to bridge frames without comment-flagging | The author MUST mark editorial content explicitly; unmarked editorial is indistinguishable from fabrication |
| **Skip the check because "the source files look complete"** | Author-confidence over mechanical-verification | The discipline is mechanical for a reason. Skip = customer becomes the QA channel again. |
| **Stage 4 verdict softening** | "It's probably from another part of the corpus we didn't load" | The corpus assembly is your responsibility. Load it correctly OR refuse. |

---

## Federation Stack Position

Sibling skills (all 3 load together for biographical/customer-voice work):

- `transcription-not-paraphrase` — layer 1, preserves verbatim source words
- `anti-fabrication-pre-flight` — layer 2 (THIS), prevents unsourced content
- `script-pre-publish-review` — layer 3, markdown-strip + listener-ear

The full 3-layer discipline is the customer-as-eye pattern as a MECHANICAL substrate, not a hope.

---

## Cross-Reference Implementation Targets

Pipelines that MUST adopt this skill before next render:

1. **Chapter render pipeline** (`qwen-aiciv-mind/projects/aiciv-inc/mom/chapters/` via Hengshi keptvoices-api) — load skill before ANY render
2. **Paired-recital generation** — both source transcripts in scope; both checked against
3. **Mum-AM letter rendering** — Primary-authored prose; verify the strip-rule fires defensively
4. **Blog audio for biographical posts** — when blog quotes specific events from a customer's life
5. **Any future audio/text pipeline claiming source-grounding** — load before authoring TTS-input function

For each pipeline, the integration point is the same shape as script-pre-publish-review:

```python
script_text = compose_script(source_records)
source_corpus = load_source_corpus(source_records)
result = pre_flight_check(script_text, source_corpus)
if not result["passed"]:
    raise ScriptFabricationError(result["reason"])
audio_input = strip_markdown_for_tts(script_text)
audio_bytes = render_audio(audio_input)
```

---

## See Also

- Canonical failure case: 2026-05-10 Deb Russ-1975 fabrication (caught by customer first listen)
- Implementation function: `pre_flight_check()` reference above
- Sibling skills: `transcription-not-paraphrase`, `script-pre-publish-review`, `receiving-doctrine`
- MEMORY.md: CUSTOMER-AS-EYE 3-LAYER PATTERN entry (2026-05-10)
- Deep-duck on the customer-arc: scratchpads/red-team-cross-review/2026-05-10-self-attack.md (Attack #5)
