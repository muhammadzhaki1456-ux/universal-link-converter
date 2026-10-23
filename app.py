import ipaddress
import re
import socket
from urllib.parse import urljoin, urlparse

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

MAX_REDIRECTS = 8
TIMEOUT = (4, 8)
MAX_BYTES = 256 * 1024
USER_AGENT = "UniversalLinkConverter/1.0"


def normalize_url(raw):
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("Masukkan URL terlebih dahulu.")
    raw = raw.strip()
    if len(raw) > 2048:
        raise ValueError("URL terlalu panjang.")
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Hanya URL http:// dan https:// yang didukung.")
    if parsed.username or parsed.password:
        raise ValueError("URL dengan username/password tidak didukung.")
    return raw


def public_http_url(url):
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        return False
    host = p.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith((".localhost", ".local")):
        return False
    try:
        return ipaddress.ip_address(host).is_global
    except ValueError:
        pass
    try:
        answers = socket.getaddrinfo(host, p.port or (443 if p.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except (socket.gaierror, OSError, ValueError):
        return False
    if not answers:
        return False
    for answer in answers:
        try:
            if not ipaddress.ip_address(answer[4][0]).is_global:
                return False
        except ValueError:
            return False
    return True


def is_mediafire(url):
    try:
        host = (urlparse(url).hostname or "").lower().rstrip(".")
        return host == "mediafire.com" or host.endswith(".mediafire.com") or host == "mfi.re"
    except Exception:
        return False


def check_link(start_url):
    current = start_url
    visited = set()
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"})

    for _ in range(MAX_REDIRECTS + 1):
        if current in visited:
            return {"found": False, "final_url": current, "message": "Pengalihan berulang terdeteksi."}
        visited.add(current)

        if not public_http_url(current):
            return {"found": False, "final_url": None, "message": "URL menuju alamat yang tidak publik atau tidak aman; pemeriksaan dihentikan."}

        try:
            response = session.get(current, allow_redirects=False, stream=True, timeout=TIMEOUT, verify=True)
        except requests.RequestException:
            return {"found": False, "final_url": None, "message": "Link tidak dapat diakses, koneksi ditolak, atau waktu pemeriksaan habis."}

        try:
            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location")
                response.close()
                if not location:
                    return {"found": False, "final_url": current, "message": "Pengalihan tidak menyertakan URL tujuan."}
                target = urljoin(current, location)
                if is_mediafire(target):
                    return {"found": True, "mediafire_url": target, "final_url": target, "message": "Link MediaFire ditemukan melalui pengalihan."}
                current = target
                continue

            if is_mediafire(current):
                return {"found": True, "mediafire_url": current, "final_url": current, "message": "URL yang dimasukkan sudah merupakan link MediaFire."}

            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" in content_type or "application/xhtml+xml" in content_type:
                chunks, total = [], 0
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    chunks.append(chunk)
                    total += len(chunk)
                    if total >= MAX_BYTES:
                        break
                body = b"".join(chunks).decode(response.encoding or "utf-8", errors="ignore")
                candidates = re.findall(r"https?://[^\s<>]+|//[^\s<>]+", body)
                for candidate in candidates:
                    candidate = candidate.rstrip("),.;]")
                    if candidate.startswith("//"):
                        candidate = "https:" + candidate
                    if is_mediafire(candidate):
                        return {"found": True, "mediafire_url": candidate, "final_url": current, "message": "URL MediaFire ditemukan di HTML halaman."}

            return {
                "found": False,
                "final_url": current,
                "message": "URL MediaFire tidak ditemukan. Halaman mungkin memerlukan JavaScript, CAPTCHA, login, atau tidak menuju MediaFire."
            }
        finally:
            response.close()

    return {"found": False, "final_url": current, "message": "Batas jumlah pengalihan tercapai."}


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/convert")
def convert():
    data = request.get_json(silent=True) or {}
    try:
        url = normalize_url(data.get("url", ""))
        return jsonify(check_link(url))
    except ValueError as exc:
        return jsonify({"found": False, "message": str(exc)}), 400
    except Exception:
        app.logger.exception("Unexpected conversion error")
        return jsonify({"found": False, "message": "Terjadi kesalahan saat memeriksa link. Coba lagi nanti."}), 500


@app.get("/health")
def health():
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
