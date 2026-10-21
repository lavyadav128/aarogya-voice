#!/usr/bin/env python3
"""
Bolna Manager Script for AarogyaVoice
Handles programmatic provisioning, updating, and triggering of Bolna voice agents.
"""

import os
import sys
import json
import argparse
import requests
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load environment variables
load_dotenv()

BOLNA_API_URL = os.getenv("BOLNA_API_URL", "https://api.bolna.ai")
BOLNA_API_KEY = os.getenv("BOLNA_API_KEY", "")
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR, "agent_config.json")
PROMPT_PATH = os.path.join(CURRENT_DIR, "system_prompt.txt")


def load_agent_payload():
    """Loads and compiles the agent configuration and system prompt."""
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
    if not os.path.exists(PROMPT_PATH):
        raise FileNotFoundError(f"Prompt file not found: {PROMPT_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        prompt_text = f.read().strip()

    # Inject system prompt
    config["agent_prompts"]["task_1"]["system_prompt"] = prompt_text

    # Update backend public URL for API tools and webhooks
    config_str = json.dumps(config)
    config_str = config_str.replace("http://localhost:8000", BACKEND_PUBLIC_URL.rstrip("/"))
    return json.loads(config_str)


def get_headers():
    if not BOLNA_API_KEY:
        print("[WARNING] BOLNA_API_KEY is not set in environment or .env file.")
    return {
        "Authorization": f"Bearer {BOLNA_API_KEY}",
        "Content-Type": "application/json"
    }


def create_agent():
    """Create a new Bolna agent via V2 API."""
    payload = load_agent_payload()
    url = f"{BOLNA_API_URL}/v2/agent"
    print(f"Creating Bolna agent at {url}...")

    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
        print(f"Response [{response.status_code}]: {response.text}")
        if response.status_code in [200, 201]:
            data = response.json()
            agent_id = data.get("agent_id") or data.get("id")
            print(f"\n[SUCCESS] Agent created successfully!")
            print(f"Agent ID: {agent_id}")
            print(f"Please add this to your .env file: BOLNA_AGENT_ID={agent_id}")
            return agent_id
        else:
            print(f"[ERROR] Failed to create agent. Check your API key and permissions.")
    except Exception as e:
        print(f"[EXCEPTION] Failed to communicate with Bolna API: {e}")


def update_agent(agent_id: str):
    """Update existing Bolna agent configuration via V2 API."""
    payload = load_agent_payload()
    url = f"{BOLNA_API_URL}/v2/agent/{agent_id}"
    print(f"Updating Bolna agent {agent_id} at {url}...")

    try:
        response = requests.put(url, headers=get_headers(), json=payload, timeout=20)
        print(f"Response [{response.status_code}]: {response.text}")
        if response.status_code in [200, 201]:
            print(f"\n[SUCCESS] Agent {agent_id} updated successfully!")
        else:
            print(f"[ERROR] Update failed.")
    except Exception as e:
        print(f"[EXCEPTION] Failed to update agent: {e}")


def trigger_outbound_call(agent_id: str, recipient_phone: str):
    """Initiates an outbound phone call via Bolna."""
    url = f"{BOLNA_API_URL}/call"
    payload = {
        "agent_id": agent_id,
        "recipient_phone_number": recipient_phone
    }
    print(f"Triggering outbound call to {recipient_phone} with agent {agent_id}...")

    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=20)
        print(f"Response [{response.status_code}]: {response.text}")
        if response.status_code in [200, 201]:
            print(f"\n[SUCCESS] Call initiated! Check your phone.")
        else:
            print(f"[ERROR] Call trigger failed.")
    except Exception as e:
        print(f"[EXCEPTION] Failed to trigger call: {e}")


def list_agents():
    """Lists all Bolna agents registered under this account."""
    url = f"{BOLNA_API_URL}/agent/all"
    print(f"Fetching agents from {url}...")

    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        print(f"Response [{response.status_code}]:")
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(response.text)
    except Exception as e:
        print(f"[EXCEPTION] Failed to list agents: {e}")


def check_account():
    """Checks Bolna user account and wallet credits."""
    url = f"{BOLNA_API_URL}/me"
    print(f"Checking account at {url}...")
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code == 200:
            data = response.json()
            print("\n[ACCOUNT DETAILS]")
            print(f"  User ID: {data.get('id')}")
            print(f"  Email: {data.get('email')}")
            print(f"  Wallet Credits: ${data.get('wallet')}")
        else:
            print(f"[ERROR] {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[EXCEPTION]: {e}")


def export_bundle():
    """Exports compiled agent configuration for Bolna dashboard import."""
    payload = load_agent_payload()
    export_path = os.path.join(CURRENT_DIR, "compiled_bolna_agent.json")
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"[EXPORT] Compiled agent payload exported to: {export_path}")
    print("You can upload this directly into the Bolna Web Dashboard (bolna.ai) if preferred.")


def main():
    parser = argparse.ArgumentParser(description="AarogyaVoice Bolna Agent Manager")
    parser.add_argument("command", choices=["create", "update", "call", "list", "me", "export"],
                        help="Action to perform")
    parser.add_argument("--agent-id", help="Bolna Agent ID (optional if set in .env)")
    parser.add_argument("--phone", help="Recipient phone number (e.g. +919876543210) for call action")

    args = parser.parse_args()

    agent_id = args.agent_id or os.getenv("BOLNA_AGENT_ID")

    if args.command == "create":
        create_agent()
    elif args.command == "update":
        if not agent_id:
            print("[ERROR] --agent-id or BOLNA_AGENT_ID in .env is required for update.")
            sys.exit(1)
        update_agent(agent_id)
    elif args.command == "call":
        if not agent_id:
            print("[ERROR] --agent-id or BOLNA_AGENT_ID in .env is required for call.")
            sys.exit(1)
        if not args.phone:
            print("[ERROR] --phone is required to trigger a call.")
            sys.exit(1)
        trigger_outbound_call(agent_id, args.phone)
    elif args.command == "list":
        list_agents()
    elif args.command == "me":
        check_account()
    elif args.command == "export":
        export_bundle()


if __name__ == "__main__":
    main()
