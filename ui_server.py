import os
import json
import asyncio
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from pathlib import Path

from core.orchestrator import Orchestrator
from config.settings import settings

orchestrator = Orchestrator()


class ATLASRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path("./ui").absolute()), **kwargs)

    def do_POST(self):
        if self.path == "/api/execute":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode('utf-8'))
                command = data.get("command", "")
                confirmed = data.get("confirmed", None)

                # Execute command via Orchestrator in asyncio loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                if confirmed is None:
                    intent = orchestrator.classify_intent(command)
                    if intent.requires_confirmation:
                        self.send_json_response({
                            "status": "requires_confirmation",
                            "prompt": f"Action '{command}' requires explicit confirmation. Proceed?"
                        })
                        return

                confirm_callback = (lambda p: confirmed) if confirmed is not None else None
                result = loop.run_until_complete(
                    orchestrator.process_command(command, confirm_fn=confirm_callback)
                )
                loop.close()

                self.send_json_response(result)

            except Exception as e:
                self.send_json_response({"status": "error", "error": str(e)}, status=500)
        else:
            self.send_error(404, "Endpoint not found")

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def log_message(self, format, *args):
        # Suppress verbose HTTP access logs in console
        pass


def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, ATLASRequestHandler)
    url = f"http://localhost:{port}"
    print("\n" + "=" * 60)
    print(f"   ATLAS UI DASHBOARD RUNNING AT: {url}")
    print(f"   Phone Connected at: {settings.phone_ip}:{settings.phone_port}")
    print("=" * 60 + "\n")
    
    # Open Dashboard in default browser
    webbrowser.open(url)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down ATLAS Dashboard.")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
