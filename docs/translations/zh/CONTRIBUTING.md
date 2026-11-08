# Contributing Guidelines / Panduan Berkontribusi

感谢您对 **opensource-agents** 的关注！我们欢迎各种形式的贡献：Bug 报告、功能请求、文档改进和代码更改。

Terima kasih atas minat Anda untuk berkontribusi. Kami menerima semua bentuk kontribusi: laporan bug, permintaan fitur, perbaikan dokumentasi, dan kode.

---

## Code of Conduct

- 保持热情、包容，并尊重所有贡献者。
- 保持讨论具有建设性，并专注于技术工作。
- 绝不容忍任何形式的骚扰或歧视。

---

## How to Contribute

### 1. Reporting Issues
- 在开启新 Issue 之前，请先检查现有的 Issue 以避免重复。
- 使用清晰、具有描述性的标题。
- 对于 Bug 报告，请包含复现步骤、预期行为与实际行为的对比，以及系统详细信息。

### 2. Pull Requests
1. Fork 仓库并从 `main` 创建您的分支：
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 进行更改：
   - Python 脚本请遵循 PEP 8 规范。
   - 在合理的地方包含 docstrings 和类型注解。
   - 如果修改了脚本，请确保适当的错误处理和日志记录。
   - 保持 YAML 工作流有效并使用并发控制。
4. 推送前在本地进行测试：
   ```bash
   # Syntax check all scripts
   python -m py_compile scripts/*.py
   ```
5. 使用描述性信息进行 Commit（例如 `feat: add retry logic to pr_reviewer.py`）。
6. 推送到您的 Fork 并提交针对 `main` 的 Pull Request。

---

## Development Guidelines

- **AI Agents**：脚本使用 `openai` v1+ 语法，并以 `gpt-4o-mini` 为目标模型，以将 API 成本保持在最低水平。
- **Prompts**：将系统 Prompt 存储在 `.github/prompts/<agent_name>.txt` 中，而不是将长字符串硬编码在 Python 代码中。
- **Secrets**：绝不能 Commit API Key 或 Token。所有脚本必须通过环境变量读取密钥。

---

## Translations

我们为 `docs/translations/` 中的文档文件维护了社区翻译：
- `id` — 印尼语 (Bahasa Indonesia)
- `zh` — 简体中文 (Simplified Chinese)
- `ja` — 日语 (日本語)
- `es` — 西班牙语 (Español)
- `ar` — 阿拉伯语 (العربية)

要触发自动化翻译更新，请为 Issue 打上 `translate` 标签，或通过 GitHub Actions 手动运行该工作流。