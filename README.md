# Jira Ticket Automation MVP

A small local-first Jira automation that receives ticket-created webhooks, claims each ticket exactly once in SQLite, and posts a canned acknowledgement comment back to Jira.

This is the a working slice of a larger ticket analyzer. The current goal is intentionally narrow: prove the webhook-to-comment loop works before adding expensive or complex analysis.
The RCA piece of this tool is currently excluded, since my original version used credentials from an internship. I'm working on updating this so it can be linked to Cursor, Claude Code, or Codex.

Used Cursor to create a simple setup script to link a repository and Cursor API account.
## What It Does

- Receives Jira Automation webhooks at `POST /jira-webhook`
- Validates a shared webhook secret
- Extracts the Jira issue key from the webhook payload
- Claims the issue key in SQLite using an atomic insert
- Skips duplicate webhook deliveries for the same issue
- Posts a canned comment to Jira
- Records completed or failed processing state locally
- Provides small local scripts for inspecting and resetting failed claims

## Current Flow

```text
Jira ticket created
  -> Jira Automation sends webhook
  -> Cloudflare Tunnel forwards to localhost
  -> webhook_handler.py validates and parses the request
  -> ticket_handler.py claims the issue key
  -> jira_api.py posts a comment to Jira
  -> ClaimTicketStore.py marks the issue completed or failed
```

## Project Files

```text
webhook_handler.py       Local HTTP server and webhook endpoint
ticket_handler.py        Main workflow: validate, claim, comment, complete/fail
ClaimTicketStore.py      SQLite-backed claim store
jira_api.py              Outgoing Jira REST API requests
jira_config.py           Local config and .env loading
setup.py                 Terminal setup for Cursor accounts and repos
cursor_config.py         Saved Cursor link config (`.cursor-link.json`)
inspect_claim.py         Inspect local claim state
reset_failed_claim.py    Reset a failed claim for retry
test_echo_server.py      Local echo server for outbound request testing
test_bot.py              Small Jira API/preflight test helper
```

## Requirements

- Python 3.12+
- A Jira Cloud site
- A Jira API token
- A Jira Automation rule
- A public tunnel for local webhook testing, such as Cloudflare Tunnel

No third-party Python packages are required for the current MVP.

## Configuration

Create a `.env` file in the repo root:

```bash
JIRA_SITE_URL=https://your-site.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=your-api-token
JIRA_WEBHOOK_SECRET=your-shared-webhook-secret
```

`jira_config.py` loads this file on import. If you edit `.env`, restart the Python process.

The repo should not commit `.env` or SQLite databases.

## Debug Mode

`jira_config.py` has a hardcoded safety switch:

```python
DEBUG_MODE = False
```

When `DEBUG_MODE` is `True`, the app avoids real Jira credentials and uses local/fake values. When `False`, it reads real values from `.env`.

This switch is deliberately not user-configurable at runtime. Posting to real Jira should require an intentional code change.

## Cursor setup

Link a Cursor account and choose repos before the webhook will start. The API key stays in `.cursor-link.json` and is not committed.

```bash
.venv/bin/python setup.py
```

Create the key at [Cursor Dashboard → Integrations](https://cursor.com/dashboard/integrations). The setup checks the key, lists repos on that account, and asks which ones to link. You can link more than one account. The last prompt activates the automation.

Until that file is activated, `webhook_handler.py` exits instead of listening.

## Running Locally

Start the webhook server:

```bash
python3 webhook_handler.py
```

It listens on:

```text
http://127.0.0.1:8001/jira-webhook
```

In another terminal, expose it with Cloudflare Tunnel:

```bash
cloudflared tunnel --url http://127.0.0.1:8001
```

Cloudflare will print a temporary public URL. Use that URL plus `/jira-webhook` in Jira Automation:

```text
https://your-temporary-url.trycloudflare.com/jira-webhook
```

## Jira Automation Rule

Create a Jira Automation rule:

```text
Trigger: Work item created
Action: Send web request
```

Recommended while testing: scope the rule to a private test project.

Configure the web request:

```text
Method: POST
URL: https://your-temporary-url.trycloudflare.com/jira-webhook
```

Headers:

```text
Content-Type: application/json
X-Jira-Automation-Secret: your-shared-webhook-secret
```

Body:

```json
{
  "issue": {
    "key": "{{issue.key}}"
  }
}
```

## Manual Webhook Test

You can test without Jira Automation:

```bash
curl -i -X POST http://127.0.0.1:8001/jira-webhook \
  -H "Content-Type: application/json" \
  -H "X-Jira-Automation-Secret: $JIRA_WEBHOOK_SECRET" \
  -d '{"issue":{"key":"JA-TEST-1"}}'
```

Expected first response:

```json
{"result": "completed"}
```

Expected duplicate response:

```json
{"result": "already_claimed"}
```

## Inspecting Local State

Inspect a claim:

```bash
python3 inspect_claim.py JA-TEST-1
```

Reset a failed claim:

```bash
python3 reset_failed_claim.py JA-TEST-1
```

Only failed claims should be reset. Completed claims are intentionally left alone to avoid duplicate Jira comments.

## Important Limitations

- This posts a normal Jira issue comment through `/rest/api/3/issue/{issue_key}/comment`.
- It does not post Jira Service Management internal/private customer comments.
- The local HTTP server handles requests simply and synchronously.
- There is no job queue yet.
- A crash after claiming but before completion can leave a ticket stuck in `processing`.
- The analysis step is not implemented yet; the comment body is currently canned.

These are acceptable constraints for the first MVP. The goal is to validate the event loop before adding analysis, retries, queues, or hosting.

## Why SQLite Claiming?

The claim store is the idempotency layer.

When a ticket is received, the app tries:

```sql
INSERT OR IGNORE INTO ticket_claims (issue_key, status)
VALUES (?, 'processing')
```

Because `issue_key` is the primary key, only one request can claim a ticket. Duplicate webhook deliveries for the same issue are skipped instead of posting duplicate comments.

## Next Milestones

- Add a tiny `analyze_ticket(issue_key)` placeholder
- Move from canned comments to structured analysis output
- Add stale `processing` claim handling
- Add real tests around claim behavior and payload validation
- Decide whether a queue is needed once analysis becomes slow

