import getpass
from pathlib import Path

from cursor_config import (
    account_label,
    load_link_config,
    repo_label,
    save_link_config,
)

try:
    from cursor_sdk import AuthenticationError, Cursor, CursorAgentError, CursorClient
except ImportError:
    AuthenticationError = None
    Cursor = None
    CursorAgentError = None
    CursorClient = None


def parse_selection(raw: str, count: int) -> list[int] | None:
    text = raw.strip().lower()
    if text in {"all", "*"}:
        return list(range(count))

    indexes: list[int] = []
    for part in text.replace(",", " ").split():
        if not part.isdigit():
            return None
        number = int(part)
        if number < 1 or number > count:
            return None
        index = number - 1
        if index not in indexes:
            indexes.append(index)

    return indexes or None


def confirm(question: str, default: bool = False) -> bool:
    suffix = "Y/n" if default else "y/N"
    answer = input(f"{question} [{suffix}]: ").strip().lower()
    if not answer:
        return default
    return answer in {"y", "yes"}


def print_status(config: dict) -> None:
    accounts = config["accounts"]
    if not accounts:
        print("No Cursor accounts linked.")
        return

    state = "active" if config.get("activated") else "not activated"
    print(f"Linked accounts ({state}):")
    for account in accounts:
        repos = account.get("repos") or []
        repo_text = ", ".join(repo_label(url) for url in repos) or "no repos"
        print(f"  {account_label(account)} — {repo_text}")


def lookup(client, api_key: str):
    try:
        user = Cursor.me(client=client, api_key=api_key)
        repos = Cursor.repositories.list(client=client, api_key=api_key)
    except AuthenticationError:
        print("That key was rejected. Check it and try again.")
        return None
    except CursorAgentError as exc:
        print(f"Could not reach Cursor: {exc.message}")
        return None

    urls = [repo.url for repo in repos if repo.url]
    return user, urls


def choose_repos(urls: list[str]) -> list[str]:
    if not urls:
        print("This account has no repos Cursor can see yet.")
        print("Connect GitHub in Cursor, then link the account again.")
        return []

    print("Repos:")
    for index, url in enumerate(urls, start=1):
        print(f"  {index}. {repo_label(url)}")

    while True:
        raw = input("Select repos (numbers, or all; blank skips): ").strip()
        if not raw:
            return []
        picked = parse_selection(raw, len(urls))
        if picked:
            return [urls[index] for index in picked]
        print("Enter one or more numbers, or all.")


def account_record(api_key: str, user, repos: list[str]) -> dict:
    name = " ".join(
        part for part in (user.user_first_name, user.user_last_name) if part
    ).strip()
    return {
        "api_key": api_key,
        "user_id": user.user_id,
        "email": user.user_email,
        "name": name,
        "api_key_name": user.api_key_name,
        "repos": repos,
    }


def upsert_account(accounts: list[dict], account: dict) -> list[dict]:
    updated = list(accounts)
    for index, existing in enumerate(updated):
        same_user = (
            account.get("user_id") is not None
            and existing.get("user_id") == account.get("user_id")
        )
        same_email = account.get("email") and existing.get("email") == account.get("email")
        if same_user or same_email:
            updated[index] = account
            print(f"Updated {account_label(account)}.")
            return updated

    updated.append(account)
    print(f"Linked {account_label(account)}.")
    return updated


def link_one(client, api_key: str) -> dict | None:
    print("Checking key...")
    found = lookup(client, api_key)
    if found is None:
        return None

    user, urls = found
    repos = choose_repos(urls)
    if not repos:
        print("Skipped this account.")
        return None

    return account_record(api_key, user, repos)


def remember(accounts: list[dict]) -> None:
    save_link_config({"activated": False, "accounts": accounts})
    print("Saved. Automation stays off until you activate it.")


def add_accounts(client, accounts: list[dict]) -> tuple[list[dict], bool]:
    edited = False

    while True:
        api_key = getpass.getpass("API key (blank to stop): ").strip()
        if not api_key:
            break

        account = link_one(client, api_key)
        if account is None:
            continue

        accounts = upsert_account(accounts, account)
        remember(accounts)
        edited = True

        if not confirm("Link another account?"):
            break

    return accounts, edited


def prompt_account_index(accounts: list[dict]) -> int | None:
    if len(accounts) == 1:
        return 0

    print("Which account?")
    for index, account in enumerate(accounts, start=1):
        print(f"  {index}. {account_label(account)}")

    raw = input("Number (blank cancels): ").strip()
    picked = parse_selection(raw, len(accounts))
    if not picked or len(picked) != 1:
        print("Cancelled.")
        return None
    return picked[0]


def reselect_repos(client, accounts: list[dict]) -> tuple[list[dict], bool]:
    if not accounts:
        print("Link an account first.")
        return accounts, False

    index = prompt_account_index(accounts)
    if index is None:
        return accounts, False

    current = accounts[index]
    found = lookup(client, current["api_key"])
    if found is None:
        print("Could not refresh repos. Link the account again with a new key.")
        return accounts, False

    _user, urls = found
    repos = choose_repos(urls)
    if not repos:
        print("Repos left unchanged.")
        return accounts, False

    updated = list(accounts)
    updated[index] = {**current, "repos": repos}
    print(f"Repos updated for {account_label(updated[index])}.")
    remember(updated)
    return updated, True


def pause_for_activation(accounts: list[dict], *, default_on: bool) -> None:
    if not accounts or not any(account.get("repos") for account in accounts):
        print("Link at least one account and one repo before activating.")
        return

    print()
    print_status({"activated": default_on, "accounts": accounts})
    activated = confirm("Activate the automation?", default=default_on)
    save_link_config({"activated": activated, "accounts": accounts})
    if activated:
        print("Activated. Start it with: python3 webhook_handler.py")
        return
    print("Saved. The automation stays off until you activate it.")


def run_setup(client) -> None:
    config = load_link_config()
    accounts = list(config["accounts"])
    edited = False
    was_activated = bool(config["activated"])

    if accounts:
        print()
        print_status(config)
        print()
        choice = input(
            "[a]dd account  [r]eselect repos  [s]tart over  [enter] continue  [q]uit: "
        ).strip().lower()

        if choice == "q":
            print("Left the current setup unchanged.")
            return
        if choice == "s":
            if not confirm("Clear every linked account?"):
                print("Left the current setup unchanged.")
                return
            accounts = []
            save_link_config({"activated": False, "accounts": []})
            print("Cleared.")
            accounts, edited = add_accounts(client, accounts)
        elif choice == "r":
            accounts, edited = reselect_repos(client, accounts)
        elif choice == "a":
            accounts, edited = add_accounts(client, accounts)
        elif choice not in {"", "c", "continue"}:
            print("Unrecognized choice. Left the current setup unchanged.")
            return
    else:
        print()
        print("Link a Cursor account, choose repos, then activate.")
        print()
        accounts, edited = add_accounts(client, accounts)

    if edited:
        print("Review the links below before turning the automation on.")

    pause_for_activation(accounts, default_on=was_activated and not edited)


def main() -> None:
    if CursorClient is None or CursorAgentError is None:
        print("cursor-sdk is not installed for this Python.")
        print("Run: .venv/bin/python setup.py")
        raise SystemExit(1)

    print("Cursor account setup")
    print("Keys are stored in .cursor-link.json and are not printed back.")
    print("Create a key at https://cursor.com/dashboard/integrations")

    try:
        print("Connecting to Cursor...")
        with CursorClient.launch_bridge(
            workspace=str(Path(__file__).resolve().parent)
        ) as client:
            run_setup(client)
    except (KeyboardInterrupt, EOFError):
        print("\nSetup cancelled.")
    except CursorAgentError as exc:
        print(f"Could not start Cursor: {exc.message}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
