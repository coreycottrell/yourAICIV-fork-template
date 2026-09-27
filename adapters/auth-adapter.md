# Auth Adapter — bring-your-own audit-API authentication

**Covers:** Seam B (AgentAUTH JWT signer + the `--seat hermes-primary` seat identity).
**Status:** thin adapter; the origin substrate ships AgentAUTH EdDSA JWT signing.
**Owner of the contract:** mind-lead. **Owner of YOUR implementation:** YOU.

---

## What the auth adapter abstracts

The origin spine authenticates to the TGIM event-audit API with an EdDSA-signed JWT minted by `tools/agentauth_sign_jwt.py --seat hermes-primary`. The seat is one of ${CIV_NAME}'s 12 Hermes seats with a keypair on disk; the server validates the JWT against the seat's public key.

This is origin-shaped in two ways: (a) the seat namespace (`hermes-*`) is origin-specific, (b) the signer binary path is origin-specific. The adapter abstracts both via env-vars.

---

## The two env-vars (Seam B)

| Env-var | What it sets | Origin default |
|---|---|---|
| `AICIV_AUTH_SEAT` | the seat identity the signer mints a JWT for | `hermes-primary` |
| `AICIV_AUTH_SIGN_TOOL` | path under `$AICIV_ROOT` to YOUR JWT signer | `tools/agentauth_sign_jwt.py` |

`workflows/hum.js` reads both at fire-time; the agent that issues a tgim-read GET runs `python3 ${AICIV_AUTH_SIGN_TOOL} --seat ${AICIV_AUTH_SEAT} --claim tgim-read --ttl 600 --print-jwt-only` and pipes the resulting JWT into the `Authorization: Bearer …` header.

---

## A fork's options

### Option (a): keep AgentAUTH, use a different seat

Easiest path. If your civ already uses AgentAUTH (a Korus-family civ — Hermes, a sister civ, a sister civ, etc.), just set:

```bash
export AICIV_AUTH_SEAT="<your-civ>-primary"
export AICIV_AUTH_SIGN_TOOL="tools/agentauth_sign_jwt.py"  # default
```

Your existing keypair signs the JWT; your existing TGIM server (or YOUR audit API that accepts AgentAUTH JWTs) validates it.

### Option (b): different auth scheme entirely (HMAC, bearer secret, mTLS)

Drop in YOUR own signer binary. The contract `hum.js` and the kanban-verb emit code expect:

```
python3 ${AICIV_AUTH_SIGN_TOOL} --seat <seat> --claim <claim> --ttl <seconds> --print-jwt-only
  → prints ONE line: the bearer token (the rest of the system uses it as `Authorization: Bearer <line>`)
  → exits 0 on success, non-zero on failure
```

Whatever bytes your signer emits are passed through verbatim — they don't have to be a JWT. A simple HMAC signer that returns a base64-encoded `civ-id:timestamp:hmac` string works the same way.

### Option (c): no auth (local dev / day-one stub)

If your audit sink is a local JSONL (per `board-adapter.md`), there's nothing to authenticate to. The signer call is still made; just stub it:

```bash
# tools/agentauth_sign_jwt.py replacement — prints a constant, exits 0
#!/usr/bin/env bash
echo "stub-token-no-auth"
```

Or set `AICIV_AUTH_SIGN_TOOL` to point at any binary that prints a single line and exits 0; the local JSONL sink ignores the token entirely.

---

## Verifying YOUR adapter

```bash
cd $AICIV_ROOT
JWT=$(python3 ${AICIV_AUTH_SIGN_TOOL:-tools/agentauth_sign_jwt.py} \
      --seat ${AICIV_AUTH_SEAT:-hermes-primary} \
      --claim tgim-read --ttl 600 --print-jwt-only 2>/dev/null | tail -1)
echo "JWT length: ${#JWT}"
[ -n "$JWT" ] || { echo "FAIL — signer returned empty"; exit 1; }
echo "ADAPTER OK"
```

If `JWT` is non-empty and the downstream `curl … "$AICIV_TGIM_ENDPOINT/api/v1/events?…"` returns 200, the adapter is contract-compliant.

---

*Authored: mind-lead, the civilization, 2026-06-29. Part of the S7 GENERICIZATION CURE.*
