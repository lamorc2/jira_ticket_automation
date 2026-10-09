from typing import Any
from collections.abc import Callable
from ClaimTicketStore import ClaimTicketStore
from cursor_sdk import Agent, AgentOptions, CloudAgentOptions, CloudRepository, CursorAgentError
from cursor_config import load_link_config
from jira_config import get_debug_mode, seen_ticket_str
from jira_api import post_internal_jira_comment, get_jira_request

def print_debug_comment(issue_key: str, body: str) -> None:
    print(f"Would comment on {issue_key}: {body}")

def analyze_ticket(issue_key: str) -> str:
    account = load_link_config()["accounts"][0]
    repo_url = account["repos"][0]
    try:
        ticket_data = get_jira_request(issue_key)
        result = Agent.prompt(
            f"Investigate Jira ticket {issue_key} and write a short analysis. Ticket: \n" + ticket_data,
            AgentOptions(
                api_key=account["api_key"],
                model="composer-2.5",
                cloud=CloudAgentOptions(repos=[CloudRepository(url=repo_url)]),
            ),
        )
    except CursorAgentError as err:
        raise RuntimeError(f"agent did not start: {err.message}") from err
    if result.status == "error":
        raise RuntimeError(f"agent run failed: {result.id}")
    return result.result



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
        analysis = analyze_ticket(issue_key)
        output_comment(issue_key, analysis)
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