import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class EchoHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        body = raw_body.decode("utf-8", errors="replace")

        print("---- incoming request ----")
        print(f"method: {self.command}")
        print(f"path: {self.path}")
        print("headers:")
        for key, value in self.headers.items():
            if key.lower() == "authorization":
                value = "<redacted>"
            print(f"  {key}: {value}")
        print("body:")
        print(body)

        response = json.dumps({"id": "fake-comment-1"}).encode("utf-8")

        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def do_GET(self) -> None:
        print("---- incoming request ----")
        print(f"method: {self.command}")
        print(f"path: {self.path}")
        print("headers:")
        for key, value in self.headers.items():
            if key.lower() == "authorization":
                value = "<redacted>"
            print(f"  {key}: {value}")

        response = json.dumps({
            "issueKey": "fake-local-request",
            "message": "GET preflight succeeded",
        }).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)



def main() -> None:
    server = HTTPServer(("127.0.0.1", 9000), EchoHandler)
    print("Echo server listening on http://127.0.0.1:9000")
    server.serve_forever()


if __name__ == "__main__":
    main()