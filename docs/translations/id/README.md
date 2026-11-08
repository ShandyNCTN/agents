# Open Source AI Agents for GitHub

> 5 autonomous GitHub Actions agents powered by OpenAI GPT-4o-mini to streamline open-source project management: issue triage, PR review, documentation sync, CI failure debugging, and multi-language community translation.

*Sistem otomasi 5 agent GitHub Actions bertenaga OpenAI GPT-4o-mini untuk mempermudah pengelolaan proyek open-source: triage issue, review PR, sinkronisasi dokumentasi & rilis, diagnosis kegagalan CI, dan penerjemahan komunitas multi-bahasa.*

---

## 🤖 5 Agent Teratas

| Agent | Workflow | Script | Trigger | Kemampuan |
|-------|----------|--------|---------|-----------|
| **1. Issue Triage** | `.github/workflows/issue-triage.yml` | `scripts/issue_triage.py` | `issues: opened` | Mengkategorikan label (`bug`, `enhancement`, `documentation`, `question`), mendeteksi issue duplikat melalui kemiripan embedding cosine, menjawab pertanyaan dengan tautan FAQ |
| **2. PR Reviewer** | `.github/workflows/pr-reviewer.yml` | `scripts/pr_reviewer.py` | `pull_request: opened, synchronize` | Menganalisis diff terpadu untuk bug, celah keamanan, pelanggaran gaya penulisan, masalah performa; memposting komentar review terstruktur; memberi peringatan jika ada test yang kurang |
| **3. Docs & Release Notes** | `.github/workflows/docs-release.yml` | `scripts/docs_release.py` | `push: main`, `release: published` | Mendeteksi deviasi dokumentasi dari commit; menghasilkan changelog markdown terstruktur dari PR yang digabungkan, memperbarui `CHANGELOG.md`, memperbarui isi rilis GitHub |
| **4. CI Debugger** | `.github/workflows/ci-debug.yml` | `scripts/ci_debug.py` | `workflow_run: completed (failure)` | Mengambil log langkah yang gagal dari zip run GitHub Actions, mendiagnosis akar masalah melalui GPT, memposting komentar pada PR atau membuat issue pelacakan dengan perbaikan yang dapat ditindaklanjuti |
| **5. Community & Translation** | `.github/workflows/community-translate.yml` | `scripts/community_translate.py` | `issues: labeled ('translate')`, `schedule (weekly)`, `pull_request: opened` | Menerjemahkan dokumentasi ke 5 bahasa (`id`, `zh`, `ja`, `es`, `ar`), menyambut kontributor baru pada PR pertama mereka |

---

## 📁 Struktur Repository

```
opensource-agents/
├── .github/
│   ├── prompts/
│   │   ├── ci_debug.txt             # System prompt: Diagnosis log CI
│   │   ├── community_translate.txt  # System prompt: Aturan terjemahan dokumen
│   │   ├── docs_release.txt         # System prompt: Changelog & analisis dokumen
│   │   ├── issue_triage.txt         # System prompt: Klasifikasi issue
│   │   └── pr_reviewer.txt          # System prompt: Kriteria review kode
│   └── workflows/
│       ├── ci-debug.yml             # Workflow Agent 4
│       ├── community-translate.yml  # Workflow Agent 5
│       ├── docs-release.yml         # Workflow Agent 3
│       ├── issue-triage.yml         # Workflow Agent 1
│       └── pr-reviewer.yml          # Workflow Agent 2
├── docs/
│   └── translations/                # Dibuat otomatis oleh Agent 5
│       ├── ar/
│       ├── es/
│       ├── id/
│       ├── ja/
│       └── zh/
├── scripts/
│   ├── ci_debug.py                  # Implementasi Agent 4
│   ├── community_translate.py       # Implementasi Agent 5
│   ├── docs_release.py              # Implementasi Agent 3
│   ├── issue_triage.py              # Implementasi Agent 1
│   └── pr_reviewer.py               # Implementasi Agent 2
├── .env.example                     # Contoh environment variables
├── CONTRIBUTING.md                  # Panduan kontribusi
├── requirements.txt                 # Dependensi Python
└── README.md
```

---

## 🚀 Petunjuk Pengaturan

### 1. Menyimpan Secret Repo GitHub

1. Buka repository Anda di GitHub.
2. Buka **Settings** > **Secrets and variables** > **Actions**.
3. Klik **New repository secret**.
4. Name: `OPENAI_API_KEY`
5. Value: API key OpenAI Anda yang dimulai dengan `sk-...`
6. Klik **Add secret**.

> **Catatan:** `GITHUB_TOKEN` dibuat dan disuntikkan secara otomatis oleh GitHub Actions untuk setiap eksekusi. Anda tidak perlu menambahkannya secara manual.

### 2. Mengaktifkan Izin Workflow

Secara default, token GitHub Actions memiliki izin baca (read-only) di repository baru. Aktifkan akses tulis:

1. Buka **Settings** > **Actions** > **General**.
2. Gulir ke bagian **Workflow permissions**.
3. Pilih **Read and write permissions**.
4. Centang **Allow GitHub Actions to create and approve pull requests**.
5. Klik **Save**.

### 3. Pengujian Lokal

Untuk menguji script secara lokal sebelum melakukan push:

```bash
# Clone repository
git clone https://github.com/your-username/opensource-agents.git
cd opensource-agents

# Menyiapkan virtual environment
python -m venv .venv
source .venv/bin/activate  # Pada Windows: .venv\Scripts\activate

# Menginstal dependensi
pip install -r requirements.txt

# Mengonfigurasi environment variables
cp .env.example .env
# Edit .env dengan OPENAI_API_KEY dan GITHUB_TOKEN Anda yang sebenarnya
```

Jalankan pemeriksaan sintaks pada semua script:

```bash
python -m py_compile scripts/*.py
```

---

## ⚙️ Konfigurasi & Kustomisasi

- **Model**: Semua script menggunakan `gpt-4o-mini` untuk waktu respons yang cepat dan biaya yang rendah. Anda dapat mengubah `model="gpt-4o-mini"` menjadi `gpt-4o` di `scripts/*.py` jika diperlukan.
- **Prompt**: Edit prompt di `.github/prompts/` agar sesuai dengan standar koding, gaya bahasa, atau label issue spesifik pada proyek Anda.
- **Ambang Batas Duplikat (Duplicate Threshold)**: Di `scripts/issue_triage.py`, sesuaikan `DUPLICATE_THRESHOLD = 0.90` (0.0 hingga 1.0) untuk mengontrol seberapa agresif issue yang mirip ditandai.
- **Bahasa Target**: Di `scripts/community_translate.py`, modifikasi `TARGET_LANGUAGES` untuk menambah atau menghapus kode bahasa.

---

## 📄 Lisensi

Lisensi MIT. Bebas digunakan dan dimodifikasi untuk proyek open-source atau komersial apa pun.