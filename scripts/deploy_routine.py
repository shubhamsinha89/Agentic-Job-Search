#!/usr/bin/env python3
"""
deploy_routine.py
Creates or updates the Claude remote routine using the generated prompt.

Prerequisites:
  1. Run build_prompt.py first  ->  agent/generated_prompt.md
  2. Fill in config/search_config.yaml  (routine.environment_id, routine.gmail_connector_uuid)
  3. Claude Code CLI must be installed and authenticated

Run:
  python scripts/deploy_routine.py
"""

import json
import subprocess
import sys
import uuid
import yaml
from pathlib import Path

ROOT = Path(__file__).parent.parent


def load_config() -> dict:
    path = ROOT / "config" / "search_config.yaml"
    if not path.exists():
        print("ERROR: config/search_config.yaml not found.")
        print("  -> Copy config/search_config.example.yaml to config/search_config.yaml")
        sys.exit(1)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_prompt() -> str:
    path = ROOT / "agent" / "generated_prompt.md"
    if not path.exists():
        print("ERROR: agent/generated_prompt.md not found.")
        print("  -> Run: python scripts/build_prompt.py")
        sys.exit(1)
    return path.read_text(encoding="utf-8").strip()


def find_claude_cli() -> str:
    candidates = [
        "claude",
        "/Users/shubhamsinha/Library/Application Support/Claude/claude-code-vm/2.1.87/claude",
        "/usr/local/bin/claude",
        "/opt/homebrew/bin/claude",
    ]
    for c in candidates:
        try:
            result = subprocess.run([c, "--version"], capture_output=True, timeout=5)
            if result.returncode == 0:
                return c
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def build_routine_body(config: dict, prompt: str, existing_id: str = None) -> dict:
    routine_cfg = config.get("routine", {})
    env_id = routine_cfg.get("environment_id", "").strip()
    gmail_uuid = routine_cfg.get("gmail_connector_uuid", "").strip()
    gmail_url = routine_cfg.get("gmail_mcp_url", "https://gmailmcp.googleapis.com/mcp/v1")

    if not env_id:
        print("ERROR: routine.environment_id is empty in search_config.yaml")
        print("  -> Set it to your Claude environment ID (e.g. env_01XXXXXXX)")
        sys.exit(1)

    body = {
        "name": "agentic-job-search-daily",
        "cron_expression": config["schedule"]["cron"],
        "enabled": True,
        "job_config": {
            "ccr": {
                "environment_id": env_id,
                "session_context": {
                    "model": "claude-sonnet-4-6",
                    "allowed_tools": ["WebSearch", "WebFetch", "Bash"],
                },
                "events": [
                    {
                        "data": {
                            "uuid": str(uuid.uuid4()),
                            "session_id": "",
                            "type": "user",
                            "parent_tool_use_id": None,
                            "message": {"role": "user", "content": prompt},
                        }
                    }
                ],
            }
        },
    }

    if gmail_uuid:
        body["mcp_connections"] = [
            {
                "connector_uuid": gmail_uuid,
                "name": "Gmail",
                "url": gmail_url,
            }
        ]

    return body


def print_manual_instructions(body: dict, existing_id: str):
    print()
    print("=" * 60)
    print("MANUAL DEPLOY INSTRUCTIONS")
    print("=" * 60)
    print()
    if existing_id:
        print(f"Update existing routine (ID: {existing_id}):")
        print("  Open Claude Code and run /schedule -> Update")
    else:
        print("Create a new routine:")
        print("  Open Claude Code and run /schedule -> Create")
    print()
    print("Paste this JSON as the routine body:")
    print()
    print(json.dumps(body, indent=2))
    print()
    print("Or paste the contents of agent/generated_prompt.md when prompted for the agent task.")


def main():
    print("Deploying agentic-job-search routine...")
    print()

    config = load_config()
    prompt = load_prompt()
    existing_id = config.get("routine", {}).get("id", "").strip()

    body = build_routine_body(config, prompt, existing_id)

    claude = find_claude_cli()
    if not claude:
        print("Claude CLI not found in PATH.")
        print_manual_instructions(body, existing_id)
        sys.exit(0)

    action = "update" if existing_id else "create"
    print(f"Claude CLI found. Action: {action}")

    if existing_id:
        deploy_prompt = (
            f"Use the RemoteTrigger tool to update routine {existing_id} "
            f"with this body: {json.dumps(body)}"
        )
    else:
        deploy_prompt = (
            f"Use the RemoteTrigger tool to create a new routine "
            f"with this body: {json.dumps(body)}"
        )

    try:
        result = subprocess.run(
            [claude, "-p", deploy_prompt],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print("Routine deployed successfully.")
            print(result.stdout)
        else:
            print("Deploy via CLI failed. Use manual instructions below.")
            print(result.stderr)
            print_manual_instructions(body, existing_id)
    except subprocess.TimeoutExpired:
        print("CLI timed out. Use manual instructions below.")
        print_manual_instructions(body, existing_id)


if __name__ == "__main__":
    main()