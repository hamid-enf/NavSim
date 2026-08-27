#!/usr/bin/env python3
"""Serve the NavSim educational video + project files for download."""
import os
import http.server
import socketserver

BASE = os.path.dirname(os.path.abspath(__file__))
PORT = 8000

VIDEO = "NavSim_educational_4K.mp4"
SIZE = os.path.getsize(os.path.join(BASE, VIDEO))

INDEX = """<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>دانلود ویدیو NavSim</title>
<body style="font-family:sans-serif;background:#0d1220;color:#e8f0ff;max-width:720px;margin:60px auto;padding:0 20px">
<h1 style="color:#56dc8c">ویدیوی آموزشی NavSim</h1>
<p>کیفیت <b>4K</b> (۳۸۴۰×۲۱۶۰) • مدت ~۱۵:۵۱ • H.264 + صدای فارسی</p>
<p style="color:#9aa">حجم فایل: <b>{size_mb:.0f} مگابایت</b></p>
<p><a href="/video" download="NavSim_educational_4K.mp4"
   style="display:inline-block;background:#56dc8c;color:#06240f;padding:16px 36px;
   border-radius:12px;font-weight:bold;text-decoration:none;font-size:20px">
   ⬇ دانلود ویدیو (4K)</a></p>
<hr style="border-color:#26304a;margin:32px 0">
<h2>فایل‌های همراه پروژه</h2>
<ul style="line-height:2">
<li><a href="/src?f=README.md" style="color:#56cdf0">README.md</a> — توضیح ساختار و بازتولید</li>
<li><a href="/src?f=narration.py" style="color:#56cdf0">narration.py</a> — متن فارسی گویندگی</li>
<li><a href="/src?f=scenes.py" style="color:#56cdf0">scenes.py</a> — تعریف ۹ صحنهٔ گرافیکی</li>
<li><a href="/src?f=lib.py" style="color:#56cdf0">lib.py</a> — موتور رندر</li>
<li><a href="/src?f=gen_data.py" style="color:#56cdf0">gen_data.py</a> — تولید دادهٔ واقعی چارت‌ها</li>
<li><a href="/src?f=build.py" style="color:#56cdf0">build.py</a> — ساخت ویدیو</li>
</ul>
</body></html>
""".format(size_mb=SIZE / (1024 * 1024))

ALLOWED = {"README.md", "narration.py", "scenes.py", "lib.py",
           "gen_data.py", "build.py"}


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, ctype, body, disp=None, length=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        if disp:
            self.send_header("Content-Disposition", disp)
        if length is not None:
            self.send_header("Content-Length", str(length))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._send(200, "text/html; charset=utf-8", INDEX.encode("utf-8"))
        elif self.path.startswith("/video"):
            path = os.path.join(BASE, VIDEO)
            size = os.path.getsize(path)
            # support Range requests so the browser can stream/seek
            rng = self.headers.get("Range")
            if rng:
                a, b = rng.replace("bytes=", "").split("-")
                a = int(a) if a else 0
                b = int(b) if b else size - 1
                self.send_response(206)
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Content-Range", f"bytes {a}-{b}/{size}")
                self.send_header("Content-Length", str(b - a + 1))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Disposition",
                                 f'attachment; filename="{VIDEO}"')
                self.end_headers()
                with open(path, "rb") as f:
                    f.seek(a)
                    rest = b - a + 1
                    while rest > 0:
                        chunk = f.read(min(1024 * 256, rest))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        rest -= len(chunk)
                return
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(size))
            self.send_header("Content-Disposition",
                             f'attachment; filename="{VIDEO}"')
            self.end_headers()
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(1024 * 256)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        elif self.path.startswith("/src"):
            import urllib.parse as up
            q = up.parse_qs(up.urlsplit(self.path).query)
            fname = q.get("f", [""])[0]
            if fname not in ALLOWED:
                self._send(403, "text/plain", b"forbidden")
                return
            path = os.path.join(BASE, fname)
            data = open(path, "rb").read()
            self._send(200, "text/plain; charset=utf-8", data,
                       disp=f'attachment; filename="{fname}"')
        else:
            self._send(404, "text/plain", b"not found")


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    with Server(("0.0.0.0", PORT), Handler) as httpd:
        print(f"serving on http://0.0.0.0:{PORT}")
        httpd.serve_forever()
