# Universal Link Converter

Website Flask untuk memeriksa pengalihan HTTP dan mencari URL MediaFire yang dapat ditemukan secara publik.

## Batasan
- Tidak mengubah link acak menjadi file MediaFire. Ia hanya menemukan URL MediaFire jika muncul di pengalihan HTTP atau URL eksplisit dalam HTML yang dapat diakses.
- Tidak menjalankan JavaScript halaman tujuan dan tidak melewati CAPTCHA, login, paywall, atau proteksi akses.
- Pemeriksaan URL publik berisiko disalahgunakan. Kode memvalidasi URL/IP publik dan memeriksa setiap pengalihan, tetapi pemeriksaan SSRF buatan sendiri tidak pernah sempurna. Untuk penggunaan skala besar, tambahkan egress firewall/proxy, rate limiting, anti-bot, serta batas penggunaan.
- Gunakan hanya untuk link yang boleh kamu periksa.

## Jalankan lokal
Memerlukan Python 3.10+.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Buka http://127.0.0.1:5000.

## Deploy gratis ke Render
1. Buat repository baru di GitHub.
2. Unggah semua file dari folder ini (jangan unggah `.venv`).
3. Di Render, pilih **New + → Blueprint** dan hubungkan repository.
4. Render membaca `render.yaml`; konfirmasi pembuatan service.
5. Setelah build selesai, buka URL publik yang diberikan Render.
6. Uji endpoint `/health` dan beberapa link yang boleh diperiksa.

Paket gratis dapat memiliki batas penggunaan dan waktu tidur saat tidak aktif; cek ketentuan terbaru Render.

## Endpoint
`POST /api/convert`, body JSON: `{"url":"https://example.com/short-link"}`

`GET /health` mengembalikan status kesehatan server.
