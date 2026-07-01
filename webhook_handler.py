import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from ClaimTicketStore import ClaimTicketStore
from ticket_handler import handle_ticket_received
from jira_config import get_webhook_secret

class JiraWebhookHandler(BaseHTTPRequestHandler):
    claim_store = ClaimTicketStore()


    def do_POST(self) -> None:
        if self.path != "/jira-webhook":
            self.send_error(404)
            return

        try:
            self._validate_webhook_secret()
            payload = self._read_json_body()
            result = handle_ticket_received(payload, self.claim_store)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid JSON"})
            return
        except KeyError as exc:
            self._send_json(400, {"error": f"missing required field: {exc}"})
            return
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
            return
        except PermissionError as exc:
            self._send_json(403, {"error": str(exc)})
            return
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
            return

        self._send_json(200, {"result": result})


    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        payload = json.loads(body)

        if not isinstance(payload, dict):
            raise ValueError("webhook payload must be a JSON object")

        return payload


    def _send_json(self, status_code: int, data: dict[str, Any]) -> None:
        body = json.dumps(data).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


    def _validate_webhook_secret(self) -> None:
        expected_secret = get_webhook_secret()
        actual_secret = self.headers.get("X-Jira-Automation-Secret")

        if actual_secret != expected_secret:
            raise PermissionError("invalid webhook secret")



def main() -> None:
    server = HTTPServer(("127.0.0.1", 8001), JiraWebhookHandler)
    print("Listening on http://127.0.0.1:8001/jira-webhook")
    server.serve_forever()


if __name__ == "__main__":
    main()