#!/usr/bin/env python3
"""
Greenhouse Export Launcher
Interactive setup wizard for credentials, then runs export.
"""

import os
import sys
from pathlib import Path
from getpass import getpass

def load_env():
    """Load environment from .env file if it exists."""
    env_file = Path.home() / ".greenhouse_export" / ".env"
    env_file.parent.mkdir(exist_ok=True)

    env_vars = {}
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, val = line.split("=", 1)
                    env_vars[key.strip()] = val.strip()

    return env_file, env_vars

def save_env(env_file, env_vars):
    """Save environment variables to .env file."""
    with open(env_file, "w") as f:
        f.write("# Greenhouse API Credentials (auto-saved from setup wizard)\n")
        for key, val in env_vars.items():
            f.write(f"{key}={val}\n")

def interactive_setup():
    """Prompt user for credentials interactively."""
    print("")
    print("═══════════════════════════════════════════════════════")
    print("  FIRST TIME SETUP — Add Your Greenhouse Credentials")
    print("═══════════════════════════════════════════════════════")
    print("")
    print("You'll need 3 pieces of info from your Greenhouse account.")
    print("This is a one-time setup — we'll save it for next time.")
    print("")
    print("🔗 Where to find them:")
    print("")
    print("   CLIENT ID & SECRET:")
    print("   • Click Settings (gear icon, top right)")
    print("   • Select 'API Credentials'")
    print("   • Look for 'OAuth2 Provider' or 'v3 OAuth'")
    print("   • Copy the CLIENT ID and CLIENT SECRET")
    print("")
    print("   USER ID:")
    print("   • Click your name/avatar (top right)")
    print("   • Select 'Profile' or 'Account Settings'")
    print("   • Look for 'User ID' (usually a number like 1234567890)")
    print("   • If not visible there, go to Settings → Users → find your name")
    print("")
    input("Ready? Press Enter to continue...")

    print("")
    client_id = input("📋 Paste v3 CLIENT ID: ").strip()
    if not client_id:
        print("❌ Cannot be empty")
        sys.exit(1)

    print("")
    client_secret = getpass("🔒 Paste v3 CLIENT SECRET (hidden): ").strip()
    if not client_secret:
        print("❌ Cannot be empty")
        sys.exit(1)

    print("")
    user_id = input("👤 Paste USER ID: ").strip()
    if not user_id:
        print("❌ Cannot be empty")
        sys.exit(1)

    return {
        "GREENHOUSE_V3_CLIENT_ID": client_id,
        "GREENHOUSE_V3_CLIENT_SECRET": client_secret,
        "GREENHOUSE_USER_ID": user_id,
    }

def main():
    print("")
    print("╔════════════════════════════════════════╗")
    print("║  Greenhouse Export Tool                ║")
    print("║  (All candidates + applications +      ║")
    print("║   resumes organized by role/dept)      ║")
    print("╚════════════════════════════════════════╝")
    print("")

    # Load or setup credentials
    env_file, env_vars = load_env()

    if env_vars and all(k in env_vars for k in ["GREENHOUSE_V3_CLIENT_ID", "GREENHOUSE_V3_CLIENT_SECRET", "GREENHOUSE_USER_ID"]):
        print("✓ Using saved credentials")
        print("")
    else:
        print("⚠ .env file not found or incomplete. Reconfiguring...")
        env_vars = interactive_setup()
        save_env(env_file, env_vars)
        print("")
        print("✓ Credentials saved")
        print("")

    # Set environment variables
    for key, val in env_vars.items():
        os.environ[key] = val

    # Import and run greenhouse_export
    print("Starting export...")
    print("")

    try:
        import greenhouse_export
        greenhouse_export.main()
    except KeyboardInterrupt:
        print("\n⚠ Export interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
