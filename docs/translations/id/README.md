# Open Source AI Agents for GitHub

> 5 autonomous GitHub Actions agents powered by OpenAI GPT-4o-mini to streamline open-source project management: issue triage, PR review, documentation sync, CI failure debugging, and multi-language community translation.

*Sistem otomasi 5 agent GitHub Actions bertenaga OpenAI GPT-4o-mini untuk mempermudah pengelolaan proyek open-source: triage issue, review PR, sinkronisasi dokumentasi & rilis, diagnosis kegagalan CI, dan penerjemahan komunitas multi-bahasa.*

---

## 🤖 The 5 Agents

| Agent | Workflow | Script | Trigger | Capabilities |
|-------|----------|--------|---------|--------------|
| **1. Issue Triage** | `.github/workflows/issue-triage.yml` | `scripts/issue_triage.py` | `issues: opened` | Mengkategorikan label (`bug`, `enhancement`, `documentation`, `question`), mendeteksi issue duplikat melalui kesamaan cosine embeddings, menjawab pertanyaan dengan tautan FAQ, **smart severity scoring** (`low`, `medium`, `high`, `critical`) dengan label SLA otomatis `sla:24h`, dan penyintesis **Automated Bug Reproduction Harness (MRE)** dengan verifikasi 1 perintah. |
| **2. PR Reviewer** | `.github/workflows/pr-reviewer.yml` | `scripts/pr_reviewer.py` | `pull_request: opened, synchronize` | Review unified diff untuk bug, gaya, dan performa; **Static Security Engine** yang memindai diff untuk secret/token/JWT/DB URI/SQLi/path traversal/eval/exec yang tertanam (hardcoded); **Auto-Test Generator** yang menyintesis suite test `pytest`/`unittest` lengkap yang dapat dijalankan untuk perubahan yang belum diuji. |
| **3. Docs & Release Notes** | `.github/workflows/docs-release.yml` | `scripts/docs_release.py` | `push: main`, `release: published` | Mendeteksi pergeseran (drift) dokumentasi dari commit; menghasilkan changelog markdown terstruktur dari PR yang digabungkan (merged), memperbarui `CHANGELOG.md` & body release GitHub; **Semantic Breaking Changes & Migration Guide** yang mendeteksi API publik yang dihapus/diubah namanya serta perubahan signature beserta panduan migrasi Sebelum/Sesudah (Before/After). |
| **4. CI Debugger** | `.github/workflows/ci-debug.yml` | `scripts/ci_debug.py` | `workflow_run: completed (failure)` | Mengambil log step yang gagal dari zip run GitHub Actions, mendiagnosis akar masalah melalui LLM; **Real Auto-Heal PR** yang secara otomatis membuat branch (`auto-fix/ci-run-<id>`), melakukan commit perbaikan file yang ditargetkan, dan membuka Pull Request beserta diagnosis dan penjelasan perbaikannya. |
| **5. Community & Translation** | `.github/workflows/community-translate.yml` | `scripts/community_translate.py` | `issues: labeled ('translate')`, `schedule (weekly)`, `pull_request: opened` | Menerjemahkan dokumentasi ke 5 bahasa (`id`, `zh`, `ja`, `es`, `ar`); **Contributor Lint & Onboarding Mentor** yang memeriksa pesan commit PR terhadap Conventional Commits, memverifikasi sinkronisasi branch, dan memberikan bimbingan (mentorship) personal yang empatik dalam bahasa ibu kontributor. |

---

## 🌟 Advanced Superpowers

### 1. Automated Bug Reproduction Harness (Issue Triage)
Saat laporan bug dibuat, agent triage menganalisis stack trace dan cuplikan kode untuk menyintesis skrip reproduksi mandiri yang dapat dijalankan (`python`, `javascript`, atau `sh`) dan mempostingnya langsung ke issue:
```bash
# 🤖 Automated Bug Reproduction Harness
# Jalankan dengan satu perintah:
python repro.py
```
Bug kritis secara otomatis menerima label `severity:critical` dan `sla:24h` untuk penanganan insiden yang dipercepat.

### 2. Auto-Test Generator & Security Rule Engine (PR Reviewer)
- **Static Security Engine**: Penambahan diff dipindai terlebih dahulu terhadap pola untuk API key, token OpenAI/GitHub/AWS, secret JWT, string koneksi database, string SQL injection, directory traversal, dan `eval`/`exec` dinamis.
- **Auto-Test Generator**: Jika perubahan kode belum memiliki unit test, reviewer akan menghasilkan suite test `pytest` atau `unittest` yang lengkap dan siap disalin untuk mencakup logika baru dan edge case.

### 3. Semantic Breaking Changes & Migration Guide (Docs & Release)
Secara otomatis mengidentifikasi breaking changes di seluruh pull request yang digabungkan (API yang diubah namanya/dihapus, signature fungsi yang diubah, variabel lingkungan yang dimodifikasi) dan menghasilkan bagian khusus `### ⚠️ Breaking Changes & Migration Guide` di dalam `CHANGELOG.md` lengkap dengan contoh migrasi Sebelum/Sesudah langkah demi langkah.

### 4. Real Auto-Heal PRs (CI Debugger)
Saat workflow CI gagal, CI debugger mendiagnosis kegagalan tersebut dan—untuk error yang ditargetkan dan dapat diperbaiki (pin dependensi, salah ketik, masalah sintaksis, impor yang rusak)—membuat branch khusus (`auto-fix/ci-run-<run_id>`), melakukan commit perbaikan menggunakan GitHub API, dan membuka Pull Request yang siap untuk direview.

### 5. Contributor Lint & Onboarding Mentor (Community & Translation)
- **Conventional Commits Lint**: Memeriksa semua subjek commit di dalam PR terhadap standar conventional commit (`feat:`, `fix:`, `docs:`, `chore:`, dll.).
- **Branch Sync Check**: Membandingkan branch PR dengan branch target dan memberikan peringatan jika branch tersebut tertinggal.
- **Localized Mentorship**: Mendeteksi bahasa utama kontributor dari lokasi/bio profil atau konten PR dan memberikan bimbingan serta panduan orientasi (onboarding) yang ramah dan dilokalisasi.

---

## 📁 Repository Structure

```
opensource-agents/
├── .github/
│   ├── prompts/
│   │   ├── ci_debug.txt             # System prompt: Diagnosis log CI
│   │   ├── community_translate.txt  # System prompt: Aturan penerjemahan dokumentasi
│   │   ├── docs_release.txt         # System prompt: Analisis changelog & dokumentasi
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
├── .env.example                     # Contoh variabel lingkungan
├── CONTRIBUTING.md                  # Panduan kontributor
├── requirements.txt                 # Dependensi Python
└── README.md
```

---

## 🚀 Setup Instructions / Petunjuk Pengaturan

### 1. Store GitHub Repo Secret

1. Buka repository Anda di GitHub.
2. Buka **Settings** > **Secrets and variables** > **Actions**.
3. Klik **New repository secret**.
4. Name: `OPENAI_API_KEY`
5. Value: API key OpenAI Anda yang dimulai dengan `sk-...`
6. Klik **Add secret**.

> **Catatan:** `GITHUB_TOKEN` secara otomatis dibuat dan diinjeksikan oleh GitHub Actions untuk setiap kali run. Anda tidak perlu menambahkannya secara manual.

### 2. Enable Workflow Permissions

Secara default, token GitHub Actions memiliki izin baca-saja (read-only) pada repository baru. Aktifkan akses tulis (write):

1. Buka **Settings** > **Actions** > **General**.
2. Gulir ke bagian **Workflow permissions**.
3. Pilih **Read and write permissions**.
4. Centang **Allow GitHub Actions to create and approve pull requests**.
5. Klik **Save**.

### 3. Local Testing

Untuk menguji skrip secara lokal sebelum melakukan push:

```bash
# Clone repository
git clone https://github.com/your-username/opensource-agents.git
cd opensource-agents

# Siapkan virtual environment
python -m venv .venv
source .venv/bin/activate  # Pada Windows: .venv\Scripts\activate

# Instal dependensi
pip install -r requirements.txt

# Konfigurasikan variabel lingkungan
cp .env.example .env
# Edit .env dengan OPENAI_API_KEY dan GITHUB_TOKEN asli Anda
```

Jalankan pemeriksaan sintaksis pada semua skrip:

```bash
python -m py_compile scripts/*.py
```

---

## ⚙️ Configuration & Customization

- **Model**: Semua skrip menggunakan `gpt-4o-mini` untuk waktu respons yang cepat dan biaya yang rendah. Anda dapat mengubah `model="gpt-4o-mini"` menjadi `gpt-4o` di dalam `scripts/*.py` jika diperlukan.
- **Prompts**: Edit prompt di dalam `.github/prompts/` agar sesuai dengan standar koding proyek Anda, nada suara (tone of voice), atau label issue tertentu.
- **Duplicate Threshold**: Di dalam `scripts/issue_triage.py`, sesuaikan `DUPLICATE_THRESHOLD = 0.90` (0.0 hingga 1.0) untuk mengontrol seberapa agresif issue yang serupa ditandai.
- **Target Languages**: Di dalam `scripts/community_translate.py`, modifikasi `TARGET_LANGUAGES` untuk menambah atau menghapus kode bahasa.

---

## 📄 License

MIT License. Bebas digunakan dan dimodifikasi untuk proyek open-source atau komersial apa pun.