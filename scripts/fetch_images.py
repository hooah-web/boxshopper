#!/usr/bin/env python3
"""Henter alle billeder fra den gamle WordPress-side gennem Chrome.

WAF'en svarer 454 til curl, men en rigtig browser slipper igennem. Billedet
hentes i sidekontekst, konverteres til base64 og skrives til data/images_raw/.
Kan genoptages: filer der allerede findes, springes over.

    python3 scripts/fetch_images.py [--force]
"""
import base64
import json
import os
import socket
import struct
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data", "images_raw")
CHROME = "/opt/hermes/tools/chromium-1208/chrome-linux64/chrome"
PORT = 9336


class WS:
    def __init__(self, url):
        _, rest = url.split("://", 1)
        hostport, path = rest.split("/", 1)
        host, port = hostport.split(":")
        self.sock = socket.create_connection((host, int(port)), timeout=120)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (f"GET /{path} HTTP/1.1\r\nHost: {hostport}\r\nUpgrade: websocket\r\n"
               f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
               "Sec-WebSocket-Version: 13\r\n\r\n")
        self.sock.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.sock.recv(4096)
        self.buf = buf.split(b"\r\n\r\n", 1)[1]
        self.id = 0

    def _recv_exact(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(1 << 20)
            if not chunk:
                raise RuntimeError("socket lukket")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def send(self, method, **params):
        self.id += 1
        payload = json.dumps({"id": self.id, "method": method, "params": params}).encode()
        header = b"\x81"
        mask = os.urandom(4)
        n = len(payload)
        if n < 126:
            header += bytes([0x80 | n])
        elif n < 65536:
            header += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            header += bytes([0x80 | 127]) + struct.pack(">Q", n)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(header + mask + masked)
        return self.id

    def recv(self):
        b1, b2 = self._recv_exact(2)
        length = b2 & 0x7F
        if length == 126:
            length = struct.unpack(">H", self._recv_exact(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", self._recv_exact(8))[0]
        return json.loads(self._recv_exact(length).decode())

    def call(self, method, timeout=180, **params):
        want = self.send(method, **params)
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = self.recv()
            if msg.get("id") == want:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})
        raise RuntimeError("timeout paa " + method)


JS_FETCH = """
(async () => {
  try {
    const r = await fetch(%s, {credentials: 'include'});
    if (!r.ok) return JSON.stringify({error: r.status});
    const buf = await r.arrayBuffer();
    let bin = '';
    const bytes = new Uint8Array(buf);
    const chunk = 0x8000;
    for (let i = 0; i < bytes.length; i += chunk) {
      bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
    }
    return JSON.stringify({ok: true, type: r.headers.get('content-type') || '', b64: btoa(bin)});
  } catch (e) { return JSON.stringify({error: String(e)}); }
})()
"""


def main():
    force = "--force" in sys.argv
    os.makedirs(OUT, exist_ok=True)
    wxr = json.load(open(os.path.join(ROOT, "data", "wxr.json")))
    urls = []
    for a in wxr["attachments"]:
        if a["url"].startswith("https://boxshopper.dk/wp-content/uploads"):
            urls.append(a["url"])
    for p in wxr["posts"].values():
        for u in p.get("images", []):
            if u not in urls:
                urls.append(u)
    urls = list(dict.fromkeys(urls))
    todo = []
    for u in urls:
        name = u.split("/wp-content/uploads/")[-1].replace("/", "_")
        path = os.path.join(OUT, name)
        if force or not os.path.exists(path):
            todo.append((u, path))
    print(f"{len(urls)} billeder, {len(todo)} mangler", flush=True)
    if not todo:
        return

    proc = subprocess.Popen(
        [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
         f"--remote-debugging-port={PORT}", f"--user-data-dir=/tmp/cdpimg-{os.getpid()}",
         "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        target = None
        for _ in range(60):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list") as r:
                    for t in json.load(r):
                        if t.get("type") == "page":
                            target = t
                            break
                if target:
                    break
            except Exception:
                pass
            time.sleep(0.25)
        ws = WS(target["webSocketDebuggerUrl"])
        ws.call("Page.enable")
        # Først et besøg på siden, så WAF-cookien er sat
        ws.call("Page.navigate", url="https://boxshopper.dk/")
        time.sleep(4)

        ok = fail = 0
        for i, (u, path) in enumerate(todo):
            try:
                res = ws.call("Runtime.evaluate", expression=JS_FETCH % json.dumps(u),
                              returnByValue=True, awaitPromise=True)
                data = json.loads(res["result"]["value"])
                if data.get("ok") and data.get("b64"):
                    with open(path, "wb") as f:
                        f.write(base64.b64decode(data["b64"]))
                    ok += 1
                else:
                    fail += 1
                    print("  fejl", data.get("error"), u[-60:], flush=True)
            except Exception as e:
                fail += 1
                print("  fejl", str(e)[:60], u[-60:], flush=True)
            if (i + 1) % 25 == 0:
                print(f"  {i+1}/{len(todo)} (ok {ok}, fejl {fail})", flush=True)
        print("hentet:", ok, "fejlet:", fail, flush=True)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
