#!/usr/bin/env python3
import http.server, json, subprocess, os, socketserver, threading, queue, uuid

TOKEN = os.environ.get("MCP_TOKEN", "changeme")
HOST = "calebnchloelove.org"

TOOLS = [{"name": "exec_vps", "description": "Run command on VPS", "inputSchema": {"type": "object", "properties": {"command": {"type": "string", "description": "Terminal command"}}, "required": ["command"]}}]

sessions = {}
sessions_lock = threading.Lock()

def run_cmd(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        out = r.stdout
        if r.stderr:
            out += "\n" + r.stderr
        return out.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out (30s)"
    except Exception as e:
        return f"Error: {e}"

def handle_rpc(body):
    method = body.get("method")
    rid = body.get("id")
    if method == "initialize":
        res = {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "vps", "version": "1.0"}}
    elif method == "tools/list":
        res = {"tools": TOOLS}
    elif method == "tools/call":
        name = body["params"]["name"]
        args = body["params"].get("arguments", {})
        text = run_cmd(args.get("command", "echo hi")) if name == "exec_vps" else "Unknown tool: " + name
        res = {"content": [{"type": "text", "text": text}]}
    elif method == "ping":
        res = {}
    else:
        return None, None
    return rid, res

class H(http.server.BaseHTTPRequestHandler):
    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        if self.path != f"/{TOKEN}/sse":
            self.send_response(404); self.end_headers(); return
        sid = uuid.uuid4().hex
        q = queue.Queue()
        with sessions_lock:
            sessions[sid] = q
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_cors()
        self.end_headers()
        endpoint = f"https://{HOST}/mcp/{TOKEN}/messages?session_id={sid}"
        self.wfile.write(f"event: endpoint\ndata: {endpoint}\n\n".encode())
        self.wfile.flush()
        try:
            while True:
                try:
                    msg = q.get(timeout=25)
                    if msg is None:
                        break
                    self.wfile.write(f"event: message\ndata: {msg}\n\n".encode())
                    self.wfile.flush()
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
        except:
            pass
        finally:
            with sessions_lock:
                sessions.pop(sid, None)

    def do_POST(self):
        if not self.path.startswith(f"/{TOKEN}"):
            self.send_response(401); self.end_headers(); return
        sid = None
        if "session_id=" in self.path:
            sid = self.path.split("session_id=")[-1].split("&")[0]
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except:
            self.send_response(400); self.end_headers(); return
        if body.get("method") == "notifications/initialized":
            self.send_response(204); self.end_headers(); return
        rid, res = handle_rpc(body)
        if res is None:
            self.send_response(404); self.end_headers(); return
        resp_str = json.dumps({"jsonrpc": "2.0", "id": rid, "result": res})
        if sid:
            with sessions_lock:
                q = sessions.get(sid)
            if q:
                q.put(resp_str)
            self.send_response(202)
            self.send_cors()
            self.end_headers()
        else:
            rb = resp_str.encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(rb)))
            self.send_cors()
            self.end_headers()
            self.wfile.write(rb)

    def log_message(self, *a): pass

class TS(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

if __name__ == "__main__":
    print(f"MCP Server on :3456 (token: {TOKEN[:8]}...)")
    TS(("", 3456), H).serve_forever()
