from typing import Any
from collections.abc import Callable
from ClaimTicketStore import ClaimTicketStore
from jira_config import get_debug_mode, seen_ticket_str
from jira_api import post_internal_jira_comment
def print_debug_comment(issue_key: str, body: str) -> None:
    print(f"Would comment on {issue_key}: {body}")


def handle_ticket_received(
    webhook_payload: dict[str, Any],
    claim_store: ClaimTicketStore,
    output_comment: Callable[[str, str], None] | None = None,
) -> str:
    issue_key = extract_issue_key(webhook_payload)
    print(f"Received webhook for {issue_key}")
    if not claim_store.claim_ticket(issue_key):
        print(f"Skipping {issue_key}: already claimed")
        return "already_claimed"

    if output_comment is None: #allows future unit tests to pass test-only functions
        output_comment = (
            print_debug_comment
            if get_debug_mode()
            else post_internal_jira_comment
        )
    try:
        output_comment(issue_key, seen_ticket_str)
    except Exception as exc:
        claim_store.mark_failed(issue_key, str(exc))
        print(f"Failed {issue_key}: {exc}")
        raise

    claim_store.mark_completed(issue_key)
    print(f"Completed {issue_key}")
    return "completed"

def extract_issue_key(webhook_payload: dict[str, Any]) -> str:
    issue = webhook_payload.get("issue")

    if not isinstance(issue, dict):
        raise ValueError("webhook payload must include an issue object")

    issue_key = issue.get("key")

    if not isinstance(issue_key, str) or not issue_key.strip():
        raise ValueError("webhook payload must include a non-empty issue key")

    return issue_key.strip()