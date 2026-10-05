# 📚 Novel Scraper API

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![License](https://img.shields.io/badge/License-MIT-green)
![Sites](https://img.shields.io/badge/Sites-3-orange)

Multi-site web novel scraper REST API — ambil data novel, daftar chapter, dan isi chapter dari **NovelUpdates**, **ScribbleHub**, dan **RoyalRoad** lewat satu API yang seragam. 🚀

> ⚠️ **PENTING — WAJIB PAKAI PROXY**
> Ketiga situs target dilindungi **Cloudflare** dan memblokir IP datacenter
> (VPS, Vercel, Railway, dsb). API akan mengembalikan `502 upstream_blocked`
> kalau dijalankan dari IP yang diblokir.
>
> **Solusi:** jalankan API ini dari IP residensial/bersih, atau set proxy:
> ```bash
> export HTTP_PROXY=http://user:pass@proxy-host:port
> export HTTPS_PROXY=http://user:pass@proxy-host:port
> ./run.sh
> ```
> Proxy residensial murah (~$5–15/bulan) sudah cukup. Tanpa ini, API hanya
> bisa dipakai untuk testing struktur, bukan scraping live.

## ✨ Fitur

- 🔍 **Search** novel lintas 3 situs sekaligus
- 📖 **Detail novel** — judul, author, cover, sinopsis, genre, status
- 📑 **Daftar chapter** lengkap dengan link
- 📄 **Isi chapter** — HTML + teks bersih, plus navigasi prev/next
- 🆕 **Latest updates** per situs
- ⏱ **Rate limiting** 2 lapis (per-IP + jeda sopan ke situs target)
- 💾 **Cache** 10 menit biar hemat request
- 📘 **OpenAPI docs** otomatis di `/docs`

## 🚀 Quick Start

```bash
git clone <repo-url>
cd novel-scraper-api
./run.sh
# → API hidup di http://0.0.0.0:8077
# → Docs: http://localhost:8077/docs
```

Butuh Python 3.10+. `run.sh` otomatis install dependencies.

## 📡 Contoh Penggunaan

**Cari novel di semua situs:**
```bash
curl "http://localhost:8077/api/v1/search?q=solo+leveling&site=all&limit=5"
```

**Detail novel:**
```bash
curl "http://localhost:8077/api/v1/novel?site=scribblehub&id=123456"
# id bisa juga full URL:
curl "http://localhost:8077/api/v1/novel?site=royalroad&id=https://www.royalroad.com/fiction/12345/slug"
```

**Daftar chapter:**
```bash
curl "http://localhost:8077/api/v1/chapters?site=scribblehub&novel_id=123456"
```

**Isi chapter:**
```bash
curl "http://localhost:8077/api/v1/chapter?site=royalroad&id=https://www.royalroad.com/fiction/12345/chapter/67890/slug"
```

**Update terbaru:**
```bash
curl "http://localhost:8077/api/v1/latest?site=royalroad&limit=10"
```

## 📋 Endpoint

| Method | Path | Parameter | Rate Limit |
|--------|------|-----------|------------|
| GET | `/health` | — | 60/menit |
| GET | `/api/v1/search` | `q`, `site`, `limit` | 30/menit |
| GET | `/api/v1/novel` | `site`, `id` | 30/menit |
| GET | `/api/v1/chapters` | `site`, `novel_id` | 20/menit |
| GET | `/api/v1/chapter` | `site`, `id` | 20/menit |
| GET | `/api/v1/latest` | `site`, `limit` | 15/menit |
| POST | `/api/v1/cache/clear` | — | — |

`site`: `scribblehub` (alias `sh`), `royalroad` (`rr`), `novelupdates` (`nu`), atau `all` (khusus search).

## 📦 Format Response

**Search** → daftar novel:
```json
{"query": "solo leveling", "site": "all",
 "results": [{"site": "scribblehub", "id": "123", "title": "...", "author": "...", "cover": "...", "url": "..."}]}
```

**Novel** → detail lengkap:
```json
{"site": "scribblehub", "id": "123", "title": "...", "author": "...",
 "synopsis": "...", "genres": ["Fantasy"], "status": "Ongoing", "url": "..."}
```

**Chapters** → `{site, novel_id, novel_title, total, chapters: [{id, title, url, published, index}]}`

**Chapter** → `{site, id, title, novel_title, content_html, content_text, url, prev_id, next_id}`

## ⏱ Rate Limiting

Dua lapis perlindungan:

1. **Ke API** (slowapi, per-IP): limit per endpoint (lihat tabel). Kelebihan → `429 {"error": "rate_limited"}`.
2. **Ke situs target**: jeda minimal **1 detik** antar request ke domain yang sama (`POLITE_DELAY` di `app/fetcher.py`) + cache 10 menit. Biar ga dikira bot dan IP ga di-ban.

## ⚠️ Catatan Cloudflare

Ketiga situs memakai proteksi Cloudflare. Jika response:
```json
{"error": "upstream_blocked", "detail": "Target site blocked this server's IP (Cloudflare)..."}
```
artinya **IP server diblokir**, bukan bug. Solusi:
- Jalankan dari IP bersih (rumah / VPS non-datacenter)
- Lewatkan via proxy residensial (`HTTP_PROXY`/`HTTPS_PROXY`)
- `app/fetcher.py` dirancang pluggable — gampang diganti ke Playwright/Selenium

## 🛠 Struktur Project

```
novel-scraper-api/
├── app/
│   ├── main.py          # Routes FastAPI + rate limit
│   ├── models.py        # Skema Pydantic
│   ├── fetcher.py       # HTTP client, cache, deteksi Cloudflare
│   └── sites/
│       ├── base.py          # Interface adapter
│       ├── scribblehub.py   # Adapter ScribbleHub
│       ├── royalroad.py     # Adapter RoyalRoad
│       └── novelupdates.py  # Adapter NovelUpdates
├── requirements.txt
├── run.sh
└── README.md
```

## 🤝 Kontribusi

PR dan issue welcome! Kalau selector HTML situs berubah (mereka sering ganti), benerin di file adapter yang sesuai.

## 📄 Lisensi

MIT — bebas pakai, modif, dan distribusi.
