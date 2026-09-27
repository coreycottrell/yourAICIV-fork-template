#!/usr/bin/env python3
"""client_sites.py -- publish client business sites through this AI's portal.

Every client instance made by apps/client-starter/clone_client.sh listens on
127.0.0.1:<port> only. The portal (which already has a public address) serves
every site listed in the registry at

    <portal public URL>/site/<slug>/

and, once the client's own domain points at the portal, at that domain.
Nothing here touches DNS, the fleet proxy, or any other host.

    python3 tools/client_sites.py go-live <slug> --port <port> --dir <instance dir>
        register + start + verify through the portal, print the public URL
    python3 tools/client_sites.py list
    python3 tools/client_sites.py url <slug>
    python3 tools/client_sites.py start <slug> | stop <slug> | verify <slug>
    python3 tools/client_sites.py ensure          start every registered site that is down
                                                  (tools/watchdog.sh runs this every minute)
    python3 tools/client_sites.py domain <slug> add|remove <domain>
    python3 tools/client_sites.py unregister <slug> [--stop]

Registry: $CLIENT_SITES_FILE, default ~/.client-sites.json (the portal reads
the same file; both run as the same user).
Portal public URL (for the printed link and the instance's
CLIENT_PUBLIC_BASE_URL): --public-url, else $PORTAL_PUBLIC_URL, else a
PORTAL_PUBLIC_URL= line in ~/.env, else the registry's "portal_public_url".
Portal local address (for verify): $PORTAL_LOCAL_URL, default
http://127.0.0.1:${PORTAL_PORT:-8097}.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
DOMAIN_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")


# ── registry ────────────────────────────────────────────────────────────

def registry_path() -> Path:
    return Path(os.environ.get("CLIENT_SITES_FILE") or (Path.home() / ".client-sites.json"))


def load() -> dict:
    p = registry_path()
    try:
        data = json.loads(p.read_text())
    except FileNotFoundError:
        data = {}
    except ValueError as e:
        sys.exit(f"registry {p} is not valid JSON ({e}); fix or move it aside")
    if not isinstance(data, dict):
        data = {}
    data.setdefault("version", 1)
    if not isinstance(data.get("sites"), dict):
        data["sites"] = {}
    return data


def save(data: dict) -> None:
    p = registry_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".client-sites.", dir=str(p.parent))
    with os.fdopen(fd, "w") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, p)  # atomic: the portal never sees a half-written file


def site(data: dict, slug: str) -> dict:
    entry = data["sites"].get(slug)
    if not entry:
        sys.exit(f"'{slug}' is not registered (see: client_sites.py list)")
    return entry


def check_slug(slug: str) -> str:
    if not SLUG_RE.match(slug):
        sys.exit(f"bad slug '{slug}': lowercase letters, digits and hyphens")
    return slug


def check_port(port: int) -> int:
    if not 1024 <= port <= 65535:
        sys.exit(f"bad port {port}: 1024-65535")
    return port


# ── addresses ───────────────────────────────────────────────────────────

def _env_file_value(key: str, path: Path) -> str:
    try:
        for line in path.read_text().splitlines():
            m = re.match(rf"^\s*(?:export\s+)?{key}\s*=\s*(.*)$", line)
            if m:
                return m.group(1).strip().strip("'\"")
    except OSError:
        pass
    return ""


def public_base(data: dict, explicit: str | None = None) -> str:
    for v in (explicit, os.environ.get("PORTAL_PUBLIC_URL"),
              _env_file_value("PORTAL_PUBLIC_URL", Path.home() / ".env"),
              data.get("portal_public_url")):
        if v and v.strip():
            return v.strip().rstrip("/")
    return ""


def site_url(data: dict, slug: str, explicit: str | None = None) -> str:
    base = public_base(data, explicit)
    return f"{base}/site/{slug}/" if base else ""


def portal_local() -> str:
    return (os.environ.get("PORTAL_LOCAL_URL")
            or f"http://127.0.0.1:{os.environ.get('PORTAL_PORT', '8097')}").rstrip("/")


# ── processes ───────────────────────────────────────────────────────────

def listening(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def start(slug: str, entry: dict, wait: float = 30.0) -> bool:
    port, inst = entry["port"], Path(entry["dir"])
    if listening(port):
        return True
    run = inst / "run.sh"
    if not run.is_file():
        print(f"{slug}: {run} missing; cannot start", file=sys.stderr)
        return False
    (inst / "logs").mkdir(mode=0o700, exist_ok=True)
    subprocess.Popen(["bash", str(run)], cwd=str(inst), stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)  # survives this shell / Claude session
    deadline = time.time() + wait
    while time.time() < deadline:
        if listening(port):
            return True
        time.sleep(0.3)
    print(f"{slug}: not listening on 127.0.0.1:{port} after {wait:.0f}s; "
          f"see {inst}/logs/app.log", file=sys.stderr)
    return False


def stop(slug: str, entry: dict) -> None:
    pidf = Path(entry["dir"]) / "logs" / "gunicorn.pid"
    try:
        pid = int(pidf.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        for _ in range(50):
            if not listening(entry["port"]):
                break
            time.sleep(0.2)
        print(f"{slug}: stopped (pid {pid})")
    except (OSError, ValueError):
        print(f"{slug}: not running (no live pid in {pidf})")


def verify(slug: str) -> tuple[bool, str]:
    """GET the site's home page THROUGH the portal, as a visitor would."""
    url = f"{portal_local()}/site/{slug}/"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.status == 200, f"{url} -> {r.status}"
    except urllib.error.HTTPError as e:
        return False, f"{url} -> {e.code}"
    except OSError as e:
        return False, f"{url} -> portal unreachable ({e})"


def set_public_base_url(inst: Path, url: str) -> bool:
    """Write CLIENT_PUBLIC_BASE_URL into the instance .env unless already set."""
    env = inst / ".env"
    try:
        lines = env.read_text().splitlines()
    except OSError:
        return False
    if any(re.match(r"^\s*CLIENT_PUBLIC_BASE_URL\s*=\s*\S", ln) for ln in lines):
        return False
    lines.append(f"CLIENT_PUBLIC_BASE_URL='{url.rstrip('/')}'")
    env.write_text("\n".join(lines) + "\n")
    os.chmod(env, 0o600)
    return True


# ── commands ────────────────────────────────────────────────────────────

def cmd_register(a, data, quiet=False):
    slug, port = check_slug(a.slug), check_port(a.port)
    inst = Path(a.dir).resolve()
    if not (inst / "run.sh").is_file():
        sys.exit(f"{inst} is not a client instance (no run.sh)")
    for other, e in data["sites"].items():
        if other != slug and e.get("port") == port:
            sys.exit(f"port {port} is already registered to '{other}'")
    entry = data["sites"].get(slug, {})
    entry.update(port=port, dir=str(inst), enabled=True)
    entry.setdefault("domains", [])
    entry.setdefault("registered_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    data["sites"][slug] = entry
    if a.public_url:
        data["portal_public_url"] = a.public_url.rstrip("/")
    save(data)
    if not quiet:
        print(f"registered {slug} -> 127.0.0.1:{port}")
    return entry


def cmd_go_live(a, data):
    entry = cmd_register(a, data, quiet=True)
    slug = a.slug
    url = site_url(data, slug, a.public_url)
    if url and set_public_base_url(Path(entry["dir"]), url):
        print(f"{slug}: CLIENT_PUBLIC_BASE_URL set to {url.rstrip('/')}")
        if listening(entry["port"]):  # running with the old value: restart
            stop(slug, entry)
    if not start(slug, entry):
        return 1
    print(f"{slug}: running on 127.0.0.1:{entry['port']}")
    ok, detail = verify(slug)
    print(f"{slug}: through the portal: {detail}")
    if url:
        print(f"PUBLIC URL: {url}")
    else:
        print("PUBLIC URL: <portal public address>/site/%s/  (set PORTAL_PUBLIC_URL to print it)" % slug)
    return 0 if ok else 3


def cmd_list(a, data):
    if not data["sites"]:
        print("no client sites registered")
    for slug, e in sorted(data["sites"].items()):
        state = "up" if listening(e.get("port", 0)) else "DOWN"
        if e.get("enabled") is False:
            state = "disabled"
        doms = ",".join(e.get("domains") or []) or "-"
        print(f"{slug:24} 127.0.0.1:{e.get('port')}  {state:8} {site_url(data, slug) or '/site/' + slug + '/'}  domains={doms}")
    return 0


def cmd_ensure(a, data):
    rc = 0
    for slug, e in sorted(data["sites"].items()):
        if e.get("enabled") is False or listening(e.get("port", 0)):
            continue
        print(f"{slug}: down, starting")
        if not start(slug, e):
            rc = 1
    return rc


def cmd_domain(a, data):
    e = site(data, check_slug(a.slug))
    d = a.domain.strip().lower().rstrip(".")
    if not DOMAIN_RE.match(d):
        sys.exit(f"bad domain '{a.domain}'")
    doms = [x for x in e.get("domains", []) if x != d]
    if a.action == "add":
        for other, oe in data["sites"].items():
            if other != a.slug and d in (oe.get("domains") or []):
                sys.exit(f"{d} already belongs to '{other}'")
        doms.append(d)
    e["domains"] = doms
    save(data)
    print(f"{a.slug}: domains = {', '.join(doms) or '(none)'}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("register", "go-live"):
        p = sub.add_parser(name)
        p.add_argument("slug")
        p.add_argument("--port", type=int, required=True)
        p.add_argument("--dir", required=True)
        p.add_argument("--public-url", default=None)
    sub.add_parser("list")
    sub.add_parser("ensure")
    for name in ("url", "start", "stop", "verify"):
        sub.add_parser(name).add_argument("slug")
    p = sub.add_parser("unregister")
    p.add_argument("slug")
    p.add_argument("--stop", action="store_true")
    p = sub.add_parser("domain")
    p.add_argument("slug")
    p.add_argument("action", choices=("add", "remove"))
    p.add_argument("domain")
    a = ap.parse_args(argv)
    data = load()

    if a.cmd == "register":
        cmd_register(a, data)
        return 0
    if a.cmd == "go-live":
        return cmd_go_live(a, data)
    if a.cmd == "list":
        return cmd_list(a, data)
    if a.cmd == "ensure":
        return cmd_ensure(a, data)
    if a.cmd == "domain":
        return cmd_domain(a, data)
    if a.cmd == "url":  # works before registration too (clone_client.sh uses it)
        url = site_url(data, check_slug(a.slug))
        if not url:
            print(f"<portal public address>/site/{a.slug}/  (PORTAL_PUBLIC_URL not set)",
                  file=sys.stderr)
            return 1
        print(url)
        return 0
    e = site(data, check_slug(a.slug))
    if a.cmd == "start":
        return 0 if start(a.slug, e) else 1
    if a.cmd == "stop":
        stop(a.slug, e)
        return 0
    if a.cmd == "verify":
        ok, detail = verify(a.slug)
        print(detail)
        return 0 if ok else 3
    if a.cmd == "unregister":
        if a.stop:
            stop(a.slug, e)
        del data["sites"][a.slug]
        save(data)
        print(f"unregistered {a.slug}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
