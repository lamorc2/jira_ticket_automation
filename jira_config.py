import os
from pathlib import Path

seen_ticket_str = "Seen by Jira automation MVP."

DEBUG_MODE = False


def load_local_env(env_path: str = ".env") -> None:
    path = Path(env_path)

    if not path.exists():
        return

    for line in path.read_text().splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        key, separator, value = line.partition("=")

        if separator != "=":
            continue

        key = key.strip()
        value = value.strip().strip('"').strip("'")

        os.environ.setdefault(key, value)

load_local_env()

def get_jira_url() -> str:
    if not DEBUG_MODE:
        return os.environ["JIRA_SITE_URL"].rstrip("/")
    else:
        return "http://127.0.0.1:9000"

def get_token() -> str:
    if not DEBUG_MODE:
        return os.environ["JIRA_API_TOKEN"]
    else:
        return "fake-token"
def get_jira_email() -> str:
    if not DEBUG_MODE:
        return os.environ["JIRA_EMAIL"]
    else:
        return "person@example.com"

def get_debug_mode() -> str:
    return DEBUG_MODE


def get_webhook_secret() -> str:
    if not DEBUG_MODE:
        return os.environ["JIRA_WEBHOOK_SECRET"]
    else:
        return "local-dev-secret"
