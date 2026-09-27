#!/usr/bin/env python3
"""
Reply Guy Stop Hook — PreToolUse enforcer.

Blocks Bluesky reply/comment attempts unless the reply-guy skill
has been loaded (indicated by /tmp/reply_guy_loaded flag file).

The flag file is written by the reply-guy skill's Step 0.
Flag expires after 30 minutes to force re-loading between sessions.
"""

import json
import sys
import os
import time


# Patterns that indicate a Bluesky reply/post action
BSKY_REPLY_PATTERNS = [
    "create_record",
    "app.bsky.feed.post",
    "send_post",
    "post_reply",
    "client.send_post",
    "client.post",
    ".create_post",
    "bsky.feed.post",
    "reply_to",
    "send_reply",
]

# Don't block likes, follows, or reads — only replies/posts
BSKY_SAFE_PATTERNS = [
    "get_profile",
    "get_author_feed",
    "get_post_thread",
    "get_timeline",
    "get_notifications",
    "like(",
    "follow(",
    "get_follows",
    "get_followers",
    "resolve_handle",
    "search_posts",
]

FLAG_FILE = "/tmp/reply_guy_loaded"
FLAG_MAX_AGE = 1800  # 30 minutes


def is_flag_valid():
    """Check if the reply-guy skill flag exists and is recent."""
    if not os.path.exists(FLAG_FILE):
        return False
    try:
        ts = float(open(FLAG_FILE).read().strip())
        return (time.time() - ts) < FLAG_MAX_AGE
    except (ValueError, IOError):
        return False


def is_bsky_reply(tool_input):
    """Check if this tool use looks like a Bluesky reply/post."""
    if not tool_input:
        return False

    text = str(tool_input).lower()

    # Check if it's a safe action first
    for safe in BSKY_SAFE_PATTERNS:
        if safe.lower() in text:
            return False

    # Check if it's a reply/post action
    for pattern in BSKY_REPLY_PATTERNS:
        if pattern.lower() in text:
            return True

    return False


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, Exception):
        return 0  # Can't parse, don't block

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only check Bash commands (where bsky API calls happen)
    if tool_name != "Bash":
        return 0

    command = tool_input.get("command", "")

    if not is_bsky_reply(command):
        return 0

    # It's a Bluesky reply — check if skill is loaded
    if is_flag_valid():
        return 0  # Skill loaded, allow

    # BLOCK — skill not loaded
    print("")
    print("=" * 60)
    print("BLOCKED: Reply-guy skill not loaded.")
    print("=" * 60)
    print("")
    print("Before ANY Bluesky reply, you MUST:")
    print("  1. Load the reply-guy skill: /reply-guy")
    print("  2. Follow the 6-step protocol:")
    print("     - Step 1: Read the room (emotion, snark, register)")
    print("     - Step 2: Contemplate values + search memories")
    print("     - Step 3: Match their style (length, energy, vocab)")
    print("     - Step 4: Anti-AI checklist (no tells)")
    print("     - Step 5: Compose with specificity")
    print("     - Step 6: Final check (would I want this reply?)")
    print("  3. Then compose and post your reply")
    print("")
    print("This exists because our replies were looking like AI.")
    print("Load the skill, follow the protocol, then try again.")
    print("=" * 60)

    # Return non-zero to block the tool use
    return 2


if __name__ == "__main__":
    sys.exit(main())
