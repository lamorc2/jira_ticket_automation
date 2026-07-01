import sys

from jira_api import get_jira_request


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 preflight_jira.py CST-123")
        return

    issue_key = sys.argv[1]
    response_body = get_jira_request(issue_key)

    print("Jira preflight succeeded")
    print(response_body[:1000])


if __name__ == "__main__":
    main()