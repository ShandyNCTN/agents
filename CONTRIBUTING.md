# Contributing Guidelines / Panduan Berkontribusi

Thank you for your interest in contributing to **opensource-agents**! We welcome contributions of all kinds: bug reports, feature requests, documentation improvements, and code changes.

Terima kasih atas minat Anda untuk berkontribusi. Kami menerima semua bentuk kontribusi: laporan bug, permintaan fitur, perbaikan dokumentasi, dan kode.

---

## Code of Conduct

- Be welcoming, inclusive, and respectful to all contributors.
- Keep discussions constructive and focused on the technical work.
- Harassment or discrimination of any form will not be tolerated.

---

## How to Contribute

### 1. Reporting Issues
- Check existing issues before opening a new one to avoid duplicates.
- Use clear, descriptive titles.
- For bug reports, include steps to reproduce, expected vs actual behavior, and system details.

### 2. Pull Requests
1. Fork the repository and create your branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Make your changes:
   - Follow PEP 8 conventions for Python scripts.
   - Include docstrings and type annotations where sensible.
   - If modifying scripts, ensure proper error handling and logging.
   - Keep YAML workflows valid and use concurrency controls.
4. Test locally before pushing:
   ```bash
   # Syntax check all scripts
   python -m py_compile scripts/*.py
   ```
5. Commit with descriptive messages (e.g. `feat: add retry logic to pr_reviewer.py`).
6. Push to your fork and submit a pull request against `main`.

---

## Development Guidelines

- **AI Agents**: Scripts use `openai` v1+ syntax and target `gpt-4o-mini` to keep API costs minimal.
- **Prompts**: Store system prompts in `.github/prompts/<agent_name>.txt` rather than embedding long strings in Python code.
- **Secrets**: NEVER commit API keys or tokens. All scripts must read secrets via environment variables.

---

## Translations

We maintain community translations for documentation files in `docs/translations/`:
- `id` — Indonesian (Bahasa Indonesia)
- `zh` — Simplified Chinese (简体中文)
- `ja` — Japanese (日本語)
- `es` — Spanish (Español)
- `ar` — Arabic (العربية)

To trigger automated translation updates, label an issue with `translate` or run the workflow manually via GitHub Actions.
