#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Install Claude Code hooks for the companion.
Reads ~/.claude/settings.json and adds Stop/UserPromptSubmit hooks.
Creates settings.json if it doesn't exist.

Usage:
  python hooks/install.py              # Install hooks
  python hooks/install.py --remove     # Remove hooks
  python hooks/install.py --dry-run    # Show what would be changed
"""

import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HOOK_FORWARDER = os.path.join(SCRIPT_DIR, "claude_hooks.py")

HOOKS_TO_INSTALL = {
    "Stop": [
        {
            "command": f"python {HOOK_FORWARDER} stop",
            "description": "Companion: forward Stop event"
        }
    ],
    "UserPromptSubmit": [
        {
            "command": f"python {HOOK_FORWARDER} user-submit",
            "description": "Companion: forward UserPromptSubmit event"
        }
    ],
}


def get_settings_paths() -> list:
    """Get possible Claude Code settings.json paths."""
    home = Path.home()

    paths = []
    # User-level settings
    paths.append(home / ".claude" / "settings.json")
    # Project-level (current directory)
    paths.append(Path.cwd() / ".claude" / "settings.json")

    return paths


def install(path: Path, dry_run: bool = False) -> bool:
    """Install hooks into settings.json at the given path."""
    print(f"\nSettings: {path}")

    # Read existing settings
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            try:
                settings = json.load(f)
            except json.JSONDecodeError as e:
                print(f"  ERROR: invalid JSON: {e}")
                return False
        print(f"  (existing file, {len(json.dumps(settings))} bytes)")
    else:
        settings = {}
        print(f"  (new file)")

    hooks = settings.setdefault("hooks", {})

    for hook_event, hook_configs in HOOKS_TO_INSTALL.items():
        existing = hooks.get(hook_event, [])
        # Check if our hook is already installed
        commands = [h.get("command", "") for h in existing]
        our_command = hook_configs[0]["command"]
        if our_command in commands:
            print(f"  {hook_event}: already installed (skipping)")
            continue

        # Remove any old companion hooks
        existing = [
            h for h in existing
            if "companion" not in h.get("description", "").lower()
            and "companion" not in h.get("command", "")
        ]
        existing.extend(hook_configs)
        hooks[hook_event] = existing
        print(f"  {hook_event}: installed")

    if dry_run:
        print("\n[Dry run] Would write:")
        print(json.dumps(settings, indent=2, ensure_ascii=False))
        return True

    # Write back
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

    print(f"  Written successfully")
    return True


def remove(path: Path, dry_run: bool = False) -> bool:
    """Remove companion hooks from settings.json."""
    if not path.exists():
        print(f"  (does not exist — nothing to remove)")
        return True

    with open(path, "r", encoding="utf-8") as f:
        try:
            settings = json.load(f)
        except json.JSONDecodeError as e:
            print(f"  ERROR: invalid JSON: {e}")
            return False

    hooks = settings.get("hooks", {})
    removed_any = False

    for hook_event, hook_configs in HOOKS_TO_INSTALL.items():
        our_command = hook_configs[0]["command"]
        existing = hooks.get(hook_event, [])
        new_hooks = [
            h for h in existing
            if h.get("command", "") != our_command
        ]
        if len(new_hooks) != len(existing):
            hooks[hook_event] = new_hooks
            removed_any = True
            print(f"  {hook_event}: removed")

    if not removed_any:
        print("  No companion hooks found")
        return True

    if dry_run:
        print("\n[Dry run] Would write:")
        print(json.dumps(settings, indent=2, ensure_ascii=False))
        return True

    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

    print(f"  Updated successfully")
    return True


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    remove_mode = "--remove" in args

    print("AI Coding Companion - Hook Installer")
    print("=" * 50)

    if not os.path.exists(HOOK_FORWARDER):
        print(f"ERROR: Hook forwarder not found: {HOOK_FORWARDER}")
        sys.exit(1)

    print(f"Forwarder: {HOOK_FORWARDER}")

    paths = get_settings_paths()
    action = "Removing from" if remove_mode else "Installing to"

    success = True
    for path in paths:
        if remove_mode:
            if not remove(path, dry_run):
                success = False
        else:
            if not install(path, dry_run):
                success = False

    if dry_run:
        print("\n[Dry run complete — no changes made]")
    elif success:
        print(f"\nDone! Hooks {'removed' if remove_mode else 'installed'}.")
        if not remove_mode:
            print("The companion daemon must be running (python main.py) for hooks to work.")
    else:
        print("\nSome operations failed. Check errors above.")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
