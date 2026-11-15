# Contributing Guidelines / Panduan Berkontribusi

Thank you for your interest in contributing to **opensource-agents**! We welcome contributions of all kinds: bug reports, feature requests, documentation improvements, and code changes.

Terima kasih atas minat Anda untuk berkontribusi. Kami menerima semua bentuk kontribusi: laporan bug, permintaan fitur, perbaikan dokumentasi, dan kode.

---

## Code of Conduct

- Bersikaplah ramah, inklusif, dan penuh hormat kepada semua kontributor.
- Jaga diskusi agar tetap membangun dan berfokus pada pekerjaan teknis.
- Pelecehan atau diskriminasi dalam bentuk apa pun tidak akan ditoleransi.

---

## How to Contribute / Cara Berkontribusi

### 1. Reporting Issues / Melaporkan Issue
- Periksa issue yang sudah ada sebelum membuka yang baru untuk menghindari duplikasi.
- Gunakan judul yang jelas dan deskriptif.
- Untuk laporan bug, sertakan langkah-langkah untuk mereproduksi, perilaku yang diharapkan vs yang terjadi, serta detail sistem.

### 2. Pull Requests
1. Lakukan fork pada repositori dan buat branch Anda dari `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Instal dependensi:
   ```bash
   pip install -r requirements.txt
   ```
3. Lakukan perubahan Anda:
   - Ikuti konvensi PEP 8 untuk skrip Python.
   - Sertakan docstring dan anotasi tipe jika diperlukan.
   - Jika memodifikasi skrip, pastikan penanganan error dan logging sudah tepat.
   - Jaga agar workflow YAML tetap valid dan gunakan kontrol konkurensi.
4. Uji secara lokal sebelum melakukan push:
   ```bash
   # Syntax check all scripts
   python -m py_compile scripts/*.py
   ```
5. Lakukan commit dengan pesan yang deskriptif (mis. `feat: add retry logic to pr_reviewer.py`).
6. Push ke fork Anda dan ajukan pull request ke branch `main`.

---

## Development Guidelines / Panduan Pengembangan

- **AI Agents**: Skrip menggunakan sintaks `openai` v1+ dan menargetkan `gpt-4o-mini` untuk menjaga biaya API tetap minimal.
- **Prompts**: Simpan system prompt di `.github/prompts/<agent_name>.txt` alih-alih menyematkan string panjang di dalam kode Python.
- **Secrets**: JANGAN PERNAH melakukan commit API key atau token. Semua skrip harus membaca secret melalui environment variables.

---

## Translations / Terjemahan

Kami memelihara terjemahan komunitas untuk file dokumentasi di `docs/translations/`:
- `id` — Indonesian (Bahasa Indonesia)
- `zh` — Simplified Chinese (简体中文)
- `ja` — Japanese (日本語)
- `es` — Spanish (Español)
- `ar` — Arabic (العربية)

Untuk memicu pembaruan terjemahan otomatis, berikan label `translate` pada issue atau jalankan workflow secara manual melalui GitHub Actions.