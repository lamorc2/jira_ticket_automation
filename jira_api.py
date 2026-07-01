import os
import base64
from jira_config import get_jira_url, get_token, get_jira_email
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
"""
All JIRA API interactions should go here, ie making comments, pulling ticket data
"""

def build_jira_auth_header() -> str:
    email = get_jira_email()
    api_token = get_token()

    raw_credentials = f"{email}:{api_token}"
    credential_bytes = raw_credentials.encode("utf-8")
    encoded_credentials = base64.b64encode(credential_bytes).decode("ascii")

    return f"Basic {encoded_credentials}"

def build_jira_headers() -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": build_jira_auth_header(),
    }


def build_internal_comment_http_request(issue_key: str, body: str) -> Request:
    site_url = get_jira_url()
    url = f"{site_url}/rest/api/3/issue/{issue_key}/comment"
    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": body,
                        }
                    ],
                }
            ],
        }
    }

    request_body = json.dumps(payload).encode("utf-8")

    return Request(
        url,
        data=request_body,
        method="POST",
        headers=build_jira_headers(),
    )


def send_jira_request(request: Request) -> tuple[int, str]:
    try:
        with urlopen(request,timeout=20) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            return response.status, response_body
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Jira returned HTTP {exc.code}: {error_body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach Jira: {exc.reason}") from exc


def post_internal_jira_comment(issue_key: str, body: str) -> None:
    request = build_internal_comment_http_request(issue_key, body)
    status_code, response_body = send_jira_request(request)

    if status_code != 201: #201 == Created
        raise RuntimeError(
            f"Unexpected Jira response HTTP {status_code}: {response_body}"
        )


def build_get_request_http_request(issue_key: str) -> Request:
    site_url = get_jira_url()
    url = f"{site_url}/rest/api/3/issue/{issue_key}"

    return Request(
        url,
        method="GET",
        headers=build_jira_headers(),
    )


def get_jira_request(issue_key: str) -> str:
    request = build_get_request_http_request(issue_key)
    status_code, response_body = send_jira_request(request)

    if status_code != 200:
        raise RuntimeError(
            f"Unexpected Jira response HTTP {status_code}: {response_body}"
        )

    return response_body