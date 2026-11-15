# Contributing Guidelines / 貢献ガイドライン

Thank you for interest in contributing to **opensource-agents**! We welcome contributions of all kinds: bug reports, feature requests, documentation improvements, and code changes.

**opensource-agents** へのご関心とご協力ありがとうございます！バグ報告、機能要望、ドキュメントの改善、コードの変更など、あらゆる形態の貢献を歓迎いたします。

---

## Code of Conduct / 行動規範

- Be welcoming, inclusive, and respectful to all contributors.
- Keep discussions constructive and focused on the technical work.
- Harassment or discrimination of any form will not be tolerated.

- すべてのコントリビューターに対して、歓迎的で、包括的であり、敬意を持って接してください。
- ディスカッションは建設的で、技術的な作業に焦点を当てたものにしてください。
- いかなる形式のハラスメントや差別も容認されません。

---

## How to Contribute / 貢献方法

### 1. Reporting Issues / イシューの報告
- Check existing issues before opening a new one to avoid duplicates.
- Use clear, descriptive titles.
- For bug reports, include steps to reproduce, expected vs actual behavior, and system details.

- 重複を防ぐため、新しいイシューを作成する前に既存のイシューを確認してください。
- 明確で説明的なタイトルを使用してください。
- バグ報告の場合は、再現手順、期待される動作と実際の動作、およびシステムの詳細を含めてください。

### 2. Pull Requests / プルリクエスト
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

1. リポジトリをフォークし、`main` からブランチを作成します:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. 依存関係をインストールします:
   ```bash
   pip install -r requirements.txt
   ```
3. 変更を加えます:
   - Pythonスクリプトでは PEP 8 規約に従ってください。
   - 適切な箇所にdocstringと型アノテーションを含めてください。
   - スクリプトを変更する場合は、適切なエラーハンドリングとロギングを行ってください。
   - YAMLワークフローを有効に保ち、同時実行制御（concurrency controls）を使用してください。
4. プッシュする前にローカルでテストを実行します:
   ```bash
   # Syntax check all scripts
   python -m py_compile scripts/*.py
   ```
5. 説明的なメッセージをつけてコミットします（例: `feat: add retry logic to pr_reviewer.py`）。
6. フォークしたリポジトリにプッシュし、`main` に対してプルリクエストを送信します。

---

## Development Guidelines / 開発ガイドライン

- **AI Agents**: Scripts use `openai` v1+ syntax and target `gpt-4o-mini` to keep API costs minimal.
- **Prompts**: Store system prompts in `.github/prompts/<agent_name>.txt` rather than embedding long strings in Python code.
- **Secrets**: NEVER commit API keys or tokens. All scripts must read secrets via environment variables.

- **AIエージェント**: APIコストを抑えるため、スクリプトは `openai` v1+ 構文を使用し、`gpt-4o-mini` をターゲットにしています。
- **プロンプト**: Pythonコード内に長い文字列を埋め込むのではなく、システムプロンプトは `.github/prompts/<agent_name>.txt` に保存してください。
- **シークレット**: APIキーやトークンを**絶対に**コミットしないでください。すべてのスクリプトは環境変数経由でシークレットを読み取る必要があります。

---

## Translations / 翻訳

We maintain community translations for documentation files in `docs/translations/`:
- `id` — Indonesian (Bahasa Indonesia)
- `zh` — Simplified Chinese (简体中文)
- `ja` — Japanese (日本語)
- `es` — Spanish (Español)
- `ar` — Arabic (العربية)

To trigger automated translation updates, label an issue with `translate` or run the workflow manually via GitHub Actions.

`docs/translations/` 内のドキュメントファイルについては、コミュニティによる翻訳を維持しています:
- `id` — インドネシア語 (Bahasa Indonesia)
- `zh` — 簡体字中国語 (简体中文)
- `ja` — 日本語 (Japanese)
- `es` — スペイン語 (Español)
- `ar` — アラビア語 (العربية)

自動翻訳の更新をトリガーするには、イシューに `translate` ラベルを付与するか、GitHub Actions経由でワークフローを手動実行してください。