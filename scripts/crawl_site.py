#!/usr/bin/env python3
"""Henter hele boxshopper.dk som HTML via lokal Chrome + CDP.

WAF'en hos Simply svarer 454 til curl og til browserens fetch i store batches,
men en rigtig Chrome-side slipper igennem. Derfor: én fane, Page.navigate pr. URL,
gem HTML paa disk. Kan genoptages (springer filer over der allerede ligger).

    python3 crawl_site.py urls.txt data/raw [--force]
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
CHROME = "/opt/hermes/tools/chromium-1208/chrome-linux64/chrome"
PORT = 9334


class WS:
    def __init__(self, url):
        _, rest = url.split("://", 1)
        hostport, path = rest.split("/", 1)
        host, port = hostport.split(":")
        self.sock = socket.create_connection((host, int(port)), timeout=60)
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
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})
        raise RuntimeError("timeout paa " + method)


def main():
    urls_file, outdir = sys.argv[1], sys.argv[2]
    force = "--force" in sys.argv
    os.makedirs(outdir, exist_ok=True)
    urls = [u.strip() for u in open(urls_file) if u.strip()]
    todo = []
    for u in urls:
        name = u.rstrip("/").split("/")[-1] or "forside"
        p = os.path.join(outdir, name + ".html")
        if force or not os.path.exists(p):
            todo.append((u, p))
    print(f"{len(urls)} URL'er, {len(todo)} mangler", flush=True)
    if not todo:
        return

    proc = subprocess.Popen(
        [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
         f"--remote-debugging-port={PORT}", f"--user-data-dir=/tmp/cdpcrawl-{os.getpid()}",
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
        if not target:
            raise RuntimeError("Chrome svarede ikke")
        ws = WS(target["webSocketDebuggerUrl"])
        ws.call("Page.enable")
        ws.call("Runtime.enable")

        done = 0
        for u, p in todo:
            for attempt in range(3):
                try:
                    ws.call("Page.navigate", url=u)
                    time.sleep(2.0)
                    html = ws.call("Runtime.evaluate",
                                   expression="document.documentElement.outerHTML",
                                   returnByValue=True)["result"].get("value") or ""
                    if len(html) > 2000:
                        with open(p, "w") as f:
                            f.write(html)
                        done += 1
                        break
                except Exception as e:
                    print("  fejl", u, str(e)[:80], flush=True)
                    time.sleep(2)
            if done % 10 == 0:
                print(f"  {done}/{len(todo)}", flush=True)
        print("gemt:", done, flush=True)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
