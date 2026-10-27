#!/usr/bin/env python3
"""Renderer udbydernes sider i Chrome og gemmer den synlige tekst.

Mange af siderne er Shopify/JS-sider, hvor priserne ikke står i HTML'en. Her
hentes den renderede tekst, så vi kan se, hvad kunden faktisk ser.

    python3 scripts/render_check.py            # alle aktive kasser
    python3 scripts/render_check.py slug ...   # udvalgte
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
CHROME = "/opt/hermes/tools/chromium-1208/chrome-linux64/chrome"
PORT = 9338
OUT = os.path.join(ROOT, "data", "render")


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

    def call(self, method, timeout=120, **params):
        want = self.send(method, **params)
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = self.recv()
            if msg.get("id") == want:
                return msg.get("result", {})
        raise RuntimeError("timeout " + method)


def main():
    k = json.load(open(os.path.join(ROOT, "src/data/kasser.json")))
    active = [b for b in k if b["status"] == "active"]
    picked = sys.argv[1:]
    if picked:
        active = [b for b in active if b["slug"] in picked]
    os.makedirs(OUT, exist_ok=True)

    proc = subprocess.Popen(
        [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
         f"--remote-debugging-port={PORT}", f"--user-data-dir=/tmp/cdprend-{os.getpid()}",
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

        out = {}
        for i, b in enumerate(active):
            url = b["provider"]["url"]
            rec = {"name": b["name"], "url": url}
            try:
                try:
                    ws.call("Page.navigate", url=url, timeout=25)
                except Exception:
                    pass
                time.sleep(3.5)
                try:
                    ws.call("Page.stopLoading", timeout=10)
                except Exception:
                    pass
                res = ws.call("Runtime.evaluate", expression="document.body ? document.body.innerText : ''",
                              returnByValue=True)
                rec["text"] = (res.get("result", {}).get("value") or "")[:12000]
                rec["final"] = ws.call("Runtime.evaluate", expression="location.href",
                                       returnByValue=True).get("result", {}).get("value", "")
            except Exception as e:
                rec["error"] = str(e)[:80]
            out[b["slug"]] = rec
            print(f"  {i+1}/{len(active)} {b['name'][:20]:20} {len(rec.get('text',''))} tegn", flush=True)
        json.dump(out, open(os.path.join(OUT, "providers.json"), "w"), ensure_ascii=False, indent=1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
