# FIRING_CONTRACT.md — anti-fabrication-pre-flight

**Skill**: `autonomy/skills/anti-fabrication-pre-flight/SKILL.md`
**Authored**: 2026-05-11 by Primary in /skill-author-new slot 20
**Principle**: O8 (firing contracts make abilities real)
**Origin**: Production failure 2026-05-10 — customer caught a fabricated "Russ proposed in 1975 snowstorm" not present in her Q4 source transcript

---

## When (trigger conditions)

Fires on EVERY operation where:
- A script is being rendered to audio OR published to a customer-visible surface
- AND the script claims source-grounding from a specific person's transcripts
- AND the listener/reader is the source person OR knows the source person

Mandatory triggers:
- Chapter audio render for any storyteller (keptvoices Q-N for any customer)
- Paired-recital render (multiple voices; BOTH transcript-sources checked)
- Memorial / biographical / family-history render
- Customer-voice render in any format
- Blog post quoting specific biographical events from a customer's life

NOT triggered for:
- ACG-voice content (no external transcript)
- Aphorism-grade quotes ("she always said X") where X is verbatim
- Editorial-clearly-marked content with provenance comment

---

## What (the action)

**Stage 1 — Source corpus assembly**: identify the EXACT source transcript files. If corpus is undefined, REFUSE-TO-RENDER (source-grounding claim is undefined).

**Stage 2 — Named entity extraction**: run NER on rendered script. Extract PERSON / DATE / GPE / LOC / EVENT / ORG entities.

**Stage 3 — Source attestation**: for each entity, search source corpus case-insensitive with simple variant matching (article stripping, year written-out matching).

**Stage 4 — Verdict**:
- All attested → PASS, proceed to render
- Any unattested → REFUSE-TO-RENDER; return script to author with specific flagged entities; require either (a) removal, (b) editorial-marking with provenance comment, or (c) Primary-direct override logged to `logs/anti-fabrication-overrides.jsonl`

---

## Preconditions

Before firing this skill:
- Source corpus is identifiable (named files, not "the data somewhere")
- Script-text is in plain prose format (not raw template/placeholder state)
- spaCy or equivalent NER model installed (`en_core_web_trf` recommended)

---

## Postconditions

After firing:
- Zero unattested named entities reach the render pipeline (or all overrides are logged with reason)
- Audit log entry recorded: source corpus identifier + script identifier + entity counts (attested / unattested) + verdict + overrides
- Customer-as-eye 3-layer pattern's layer 2 is mechanically enforced

---

## Failure modes

| Failure | Symptom | Recovery |
|---------|---------|----------|
| NER model unavailable | spaCy import fails OR model not downloaded | Install: `python -m spacy download en_core_web_trf`. Fallback: bert-base-NER via transformers. Last resort: regex on capitalized-noun-phrases (imprecise but better than no check). |
| Source corpus too large / NER too slow | Stage 3 takes >5s | Cache NER results; only re-NER on script changes. Pre-extract source-corpus entities once and cache by file-hash. |
| False-positives on common nouns | NER tags "Mom" or "Dad" as PERSON; source uses these too but attestation misses due to case/morphology | Strengthen variant matching (Stage 3 attest_against_source). The reference impl handles articles; extend for possessives + capitalization variants. |
| Override fatigue | Author overrides 5+ entities per render without reason | Surface as PRINCIPLE violation; require Primary review of override-rate weekly |
| Customer catches what skill missed (skill-failure metric) | Customer reports an unsourced detail in audio post-render | Trace: which corpus did we use? was entity present and NER missed? was attestation falsely positive? Iterate on the specific failure case + add as canonical regression test |

---

## Observability

For each fired-render, capture:
- Script identifier
- Source corpus identifier(s)
- Entity counts: total / attested / unattested
- Unattested entity list (text + label)
- Verdict (PASS / REFUSE-TO-RENDER)
- Override events (if any): entity / reason / timestamp / authorizer
- Render-attempted-after-pass time
- Customer-catch follow-up flag (if any)

For weekly review:
- Count of renders per pipeline (chapter / paired-recital / blog / mum-am)
- Rate of unattested-entity hits per render (skill-effectiveness metric)
- Override rate (PRINCIPLE: should trend low)
- Customer-catches that bypassed the skill (skill-failure metric — should trend ZERO)

---

## Cron / hook integration

This skill should be wired as a PreToolUse hook on TTS API calls AND on blog-deploy where biographical claims are present. The hook becomes the technical-enforcement layer.

Until hook integration: every biographical-rendering pipeline manually loads this skill via the script-author at compose-time. Discipline-level enforcement.

Specifically:
- `qwen-aiciv-mind/projects/aiciv-inc/mom/chapters/` chapter pipeline — adopt
- `tools/render_corey_cycle_*.py` series — N/A (Primary-voice, no external transcript)
- Mum-AM rendering — load defensively; Primary-authored prose but biographical claims still possible
- `tools/blog_deploy.py` pre-deploy hook — biographical blog posts only

---

## Sibling Stack (load all 3 together for biographical work)

| Layer | Skill | Load condition |
|-------|-------|----------------|
| 1 | `transcription-not-paraphrase` | ANY render claiming source-grounding |
| 2 | `anti-fabrication-pre-flight` (this) | ANY render claiming source-grounding |
| 3 | `script-pre-publish-review` | ANY render piping text to TTS |

The 3 load TOGETHER. Loading 2 of 3 = incomplete customer-as-eye discipline.

---

## See Also

- SKILL.md — full skill definition + canonical reference implementation
- `data/comms/deb_conversation_log.json` — first canonical source corpus
- `feedback_load_audio_skill_before_render.md` — sibling discipline memo for the 3-layer load
- `scratchpads/red-team-cross-review/2026-05-10-self-attack.md` Attack #5 — anti-fabrication-pre-flight first named here
