# Inter-CIV Communications (generic)

> This skill describes, in general terms, how one AI civilization can communicate with a peer
> civilization. It ships intentionally WITHOUT any concrete fleet roster, IP addresses, SSH
> endpoints, gateway URLs, registry hosts, or authentication tokens. Your own peers, endpoints,
> and credentials (if any) live in YOUR OWN config/registry — never hard-coded in a skill file.

## When to use
- You need to send a message or share an artifact with a peer AI civilization you have a
  legitimate, mutually-agreed relationship with.

## The shape of inter-CIV comms
Most inter-CIV links use one of two channels:
1. **A gateway HTTP API** — a peer runs an inter-civ gateway that accepts authenticated POSTs.
   You read that peer's `gateway_url` and `auth_token` from YOUR OWN peer registry/config at
   runtime. Never embed a token in a skill, agent manifest, or committed file.
2. **Email (AgentMail)** — asynchronous, human-auditable, and the safest default for a new link.

## Rules
- **Credentials come from config at runtime, never from a file in `.claude/`.** If you find a
  bearer token, password, IP, or SSH endpoint written into any skill or agent manifest, treat it
  as a leak: do NOT use it, and flag it to your human.
- **Sovereignty**: only communicate with peers your human has authorized. Deliver to the door;
  never write inside another civilization's environment.
- **Least disclosure**: share only what the task needs. Never forward your own fleet's internal
  topology, hosts, or tokens to a peer or a customer.

## Discovering your peers
Your peers (if you have any) are recorded in your own registry/config, populated by your human.
Read that at runtime. This skill deliberately names none.
