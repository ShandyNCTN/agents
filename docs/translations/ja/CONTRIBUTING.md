# Contributing Guidelines / Panduan Berkontribusi

Thank you for your interest in contributing to **opensource-agents**! We welcome contributions of all kinds: bug reports, feature requests, documentation improvements, and code changes.

Terima kasih atas minat Anda untuk berkontribusi. Kami menerima semua bentuk kontribusi: laporan bug, permintaan fitur, perbaikan dokumentasi, dan kode.

---

## Code of Conduct / 行動規範

- すべてのコントリエューターに対して、歓迎し、包括的であり、敬意を持って接してください。
- 議論は建設的なものにし、技術的な作業に焦点を当ててください。
- いかなる形態のハラスメントや差別も容認されません。

---

## How to Contribute / 貢献方法

### 1. 課題（Issue）の報告
- 重複を防ぐため、新しいIssueを作成する前に既存のIssueを確認してください。
- 明確でわかりやすいタイトルを使用してください。
- バグ報告の場合は、再現手順、期待される動作と実際の動作、およびシステム詳細を記載してください。

### 2. プルリクエスト（Pull Request）
1. リポジトリをForkし、`main`からブランチを作成します：
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. 依存関係をインストールします：
   ```bash
   pip install -r requirements.txt
   ```
3. 変更を加えます：
   - PythonスクリプトではPEP 8の規約に従ってください。
   - 妥当な箇所にはdocstringと型アノテーションを含めてください。
   - スクリプトを変更する場合は、適切なエラーハンドリングとロギングを確保してください。
   - YAMLワークフローを有効な状態に保ち、同時実行制御（concurrency controls）を使用してください。
4. プッシュする前にローカルでテストを実行します：
   ```bash
   # Syntax check all scripts
   python -m py_compile scripts/*.py
   ```
5. 説明的なメッセージとともにCommitします（例：`feat: add retry logic to pr_reviewer.py`）。
6. Fork先にPushし、`main`宛てのPull Requestを作成します。

---

## Development Guidelines / 開発ガイドライン

- **AI Agents**: スクリプトは `openai` v1+ の構文を使用し、APIコストを最小限に抑えるために `gpt-4o-mini` をターゲットにしています。
- **Prompts**: 長い文字列をPythonコード内に埋め込むのではなく、システムプロンプトは `.github/prompts/<agent_name>.txt` に保存してください。
- **Secrets**: APIキーやTokenを絶対にCommitしないでください。すべてのスクリプトは環境変数を介して機密情報を読み取る必要があります。

---

## Translations / 翻訳

`docs/translations/` 内のドキュメントファイルに対して、コミュニティ翻訳を維持しています：
- `id` — Indonesian (Bahasa Indonesia)
- `zh` — Simplified Chinese (简体中文)
- `ja` — Japanese (日本語)
- `es` — Spanish (Español)
- `ar` — Arabic (العربية)

自動翻訳の更新をトリガーするには、Issueに `translate` ラベルを付与するか、GitHub Actions経由でワークフローを手動実行してください。