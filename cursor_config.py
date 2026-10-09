import json
import os
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / ".cursor-link.json"


def load_link_config() -> dict:
    if not CONFIG_PATH.exists():
        return {"activated": False, "accounts": []}

    data = json.loads(CONFIG_PATH.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{CONFIG_PATH.name} must be a JSON object")

    accounts = data.get("accounts", [])
    if not isinstance(accounts, list):
        raise ValueError(f"{CONFIG_PATH.name} accounts must be a list")

    return {
        "activated": bool(data.get("activated")),
        "accounts": accounts,
    }


def save_link_config(config: dict) -> None:
    payload = {
        "activated": bool(config.get("activated")),
        "accounts": list(config.get("accounts", [])),
    }
    CONFIG_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    os.chmod(CONFIG_PATH, 0o600)


def account_label(account: dict) -> str:
    name = str(account.get("name") or "").strip()
    email = str(account.get("email") or "").strip() or "unknown account"
    if name:
        return f"{name} <{email}>"
    return email


def repo_label(url: str) -> str:
    cleaned = str(url).removesuffix(".git")
    marker = "github.com/"
    if marker in cleaned:
        return cleaned.split(marker, 1)[1]
    return str(url)


def activation_error() -> str | None:
    try:
        config = load_link_config()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return f"Cursor link config is unreadable ({exc}). Run: python3 setup.py"

    accounts = config["accounts"]
    if not accounts:
        return "No Cursor account is linked. Run: python3 setup.py"

    if not any(account.get("repos") for account in accounts):
        return "No repos are linked. Run: python3 setup.py"

    if not config["activated"]:
        return "Automation is not activated. Run: python3 setup.py"

    return None
