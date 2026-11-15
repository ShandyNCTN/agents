# Open Source AI Agents for GitHub

> 5 autonomous GitHub Actions agents powered by OpenAI GPT-4o-mini to streamline open-source project management: issue triage, PR review, documentation sync, CI failure debugging, and multi-language community translation.

*نظام أتمتة يتكون من 5 وكلاء (Agents) عبر GitHub Actions مدعومين بواسطة OpenAI GPT-4o-mini لتسهيل إدارة مشاريع المصادر المفتوحة: فرز المشكلات، مراجعة طلبات السحب (PR)، مزامنة التوثيق والإصدارات، تشخيص أخطاء التكامل المستمر (CI)، والترجمة المجتمعية متعددة اللغات.*

---

## 🤖 The 5 Agents

| Agent | Workflow | Script | Trigger | Capabilities |
|-------|----------|--------|---------|--------------|
| **1. Issue Triage** | `.github/workflows/issue-triage.yml` | `scripts/issue_triage.py` | `issues: opened` | تصنيف التسميات (`bug`, `enhancement`, `documentation`, `question`)، اكتشاف المشكلات المكررة عبر تشابه التضمينات (cosine embeddings)، الإجابة على الأسئلة بروابط الأسئلة الشائعة (FAQ)، **تسجيل درجات الخطورة الذكية** (`low`, `medium`, `high`, `critical`) مع تسميات اتفاقية مستوى الخدمة التلقائية `sla:24h`، ومولد **أداة إعادة إنتاج الأخطاء الآلية (MRE)** مع التحقق بأمر واحد. |
| **2. PR Reviewer** | `.github/workflows/pr-reviewer.yml` | `scripts/pr_reviewer.py` | `pull_request: opened, synchronize` | مراجعة الفروق الموحدة (Unified diff) للأخطاء، النمط، والأداء؛ **محرك الأمان الثابت** الذي يفحص الفروق بحثاً عن الأسرار المضمنة/الرموز/JWTs/روابط قواعد البيانات/حقن SQL/اجتاز المسار/eval/exec؛ **مولد الاختبارات التلقائي** الذي ينشئ مجموعات اختبار `pytest`/`unittest` كاملة وقابلة للتنفيذ للتغييرات غير المختبرة. |
| **3. Docs & Release Notes** | `.github/workflows/docs-release.yml` | `scripts/docs_release.py` | `push: main`, `release: published` | اكتشاف انحراف التوثيق من الالتزامات (commits)؛ إنتاج سجلات التغيير المنظمة بلغة markdown من طلبات السحب المدمجة، تحديث `CHANGELOG.md` ونص إصدار GitHub؛ **التغييرات الكبرى الدلالية ودليل الهجرة** الذي يكتشف واجهات برمجة التطبيقات العامة المحذوفة/المعاد تسميتها وتغييرات التوقيع مع أدلة هجرة قبل/بعد. |
| **4. CI Debugger** | `.github/workflows/ci-debug.yml` | `scripts/ci_debug.py` | `workflow_run: completed (failure)` | جلب سجلات الخطوات الفاشلة من ملف zip لتشغيل GitHub Actions، تشخيص السبب الجذري عبر نموذج اللغات الكبير (LLM)؛ **طلب سحب الإصلاح الذاتي الحقيقي** الذي ينشئ فرعاً تلقائياً (`auto-fix/ci-run-<id>`)، يلتزم بإصلاح الملف المستهدف، ويفتح طلب سحب مع التشخيص وشرح الإصلاح. |
| **5. Community & Translation** | `.github/workflows/community-translate.yml` | `scripts/community_translate.py` | `issues: labeled ('translate')`, `schedule (weekly)`, `pull_request: opened` | ترجمة التوثيق إلى 5 لغات (`id`, `zh`, `ja`, `es`, `ar`)؛ **مرشد التدقيق والتوجيه للمساهمين** الذي يتحقق من رسائل الالتزام الخاصة بطلبات السحب مقابل معايير الالتزامات التقليدية (Conventional Commits)، ويتحقق من مزامنة الفروع، ويقدم إرشاداً تعاطفياً ومخصصاً بلغة المساهم الأم. |

---

## 🌟 Advanced Superpowers

### 1. Automated Bug Reproduction Harness (Issue Triage)
عند تقديم تقرير خطأ، يقوم وكيل الفرز بتحليل مسارات التكدس (stack traces) ومقتطفات الكود لتركيب نص برمجي مستقل وقابل للتنفيذ لإعادة الإنتاج (`python`، `javascript`، أو `sh`) وينشره مباشرة في المشكلة:
```bash
# 🤖 Automated Bug Reproduction Harness
# Run with one command:
python repro.py
```
تحصل الأخطاء الحرجة تلقائياً على تسميات `severity:critical` و `sla:24h` للاستجابة السريعة للحوادث.

### 2. Auto-Test Generator & Security Rule Engine (PR Reviewer)
- **محرك الأمان الثابت (Static Security Engine)**: تتم مراجعة إضافات الفروق مسبقاً بحثاً عن أنماط لمفاتيح API، رموز OpenAI/GitHub/AWS، أسرار JWT، سلاسل الاتصال بقواعد البيانات، سلاسل حقن SQL، اجتياز الدلائل، و `eval`/`exec` الديناميكي.
- **مولد الاختبارات التلقائي (Auto-Test Generator)**: إذا كانت تغييرات الكود تفتقر إلى اختبارات الوحدة، يقوم المراجع بإنشاء مجموعة اختبار `pytest` أو `unittest` كاملة وقابلة للنسخ واللصق تغطي المنطق الجديد والحالات الحدية (edge cases).

### 3. Semantic Breaking Changes & Migration Guide (Docs & Release)
يحدد تلقائياً التغييرات الكبرى عبر طلبات السحب المدمجة (واجهات برمجة التطبيقات المعاد تسميتها/المحذوفة، تواقيع الدوال المعدلة، متغيرات البيئة المعدلة) وينشئ قسماً مخصصاً `### ⚠️ Breaking Changes & Migration Guide` في ملف `CHANGELOG.md` مع أمثلة هجرة خطوة بخطوة قبل/بعد.

### 4. Real Auto-Heal PRs (CI Debugger)
عند فشل سير عمل التكامل المستمر (CI)، يقوم منقح CI بتشخيص الفشل — وللأخطاء المستهدفة والقابلة للإصلاح (تثبيت التبعيات، الأخطاء الإملائية، أخطاء النحو، الواردات المكسورة) — بإنشاء فرع مخصص (`auto-fix/ci-run-<run_id>`)، والالتزام بالإصلاح باستخدام GitHub API، وفتح طلب سحب جاهز للمراجعة.

### 5. Contributor Lint & Onboarding Mentor (Community & Translation)
- **تدقيق الالتزامات التقليدية (Conventional Commits Lint)**: يفحص جميع عناوين الالتزامات في طلب السحب مقابل معايير الالتزامات التقليدية (`feat:`, `fix:`, `docs:`, `chore:`, إلخ).
- **فحص مزامنة الفروع (Branch Sync Check)**: يقارن فرع طلب السحب بالفرع المستهدف ويحذر إذا تأخر عنه.
- **الإرشاد المحلي (Localized Mentorship)**: يكتشف اللغة الأساسية للمساهم من موقع الملف الشخصي/السيرة الذاتية أو محتوى طلب السحب ويقدم توجيه إرشاد وترحيب دافئ ومحلي.

---

## 📁 Repository Structure

```
opensource-agents/
├── .github/
│   ├── prompts/
│   │   ├── ci_debug.txt             # System prompt: CI log diagnosis
│   │   ├── community_translate.txt  # System prompt: Docs translation rules
│   │   ├── docs_release.txt         # System prompt: Changelog & docs analysis
│   │   ├── issue_triage.txt         # System prompt: Issue classification
│   │   └── pr_reviewer.txt          # System prompt: Code review criteria
│   └── workflows/
│       ├── ci-debug.yml             # Agent 4 workflow
│       ├── community-translate.yml  # Agent 5 workflow
│       ├── docs-release.yml         # Agent 3 workflow
│       ├── issue-triage.yml         # Agent 1 workflow
│       └── pr-reviewer.yml          # Agent 2 workflow
├── docs/
│   └── translations/                # Auto-generated by Agent 5
│       ├── ar/
│       ├── es/
│       ├── id/
│       ├── ja/
│       └── zh/
├── scripts/
│   ├── ci_debug.py                  # Agent 4 implementation
│   ├── community_translate.py       # Agent 5 implementation
│   ├── docs_release.py              # Agent 3 implementation
│   ├── issue_triage.py              # Agent 1 implementation
│   └── pr_reviewer.py               # Agent 2 implementation
├── .env.example                     # Sample environment variables
├── CONTRIBUTING.md                  # Contributor guidelines
├── requirements.txt                 # Python dependencies
└── README.md
```

---

## 🚀 Setup Instructions / Petunjuk Pengaturan

### 1. Store GitHub Repo Secret

1. Open your repository on GitHub.
2. Go to **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret**.
4. Name: `OPENAI_API_KEY`
5. Value: Your OpenAI API key starting with `sk-...`
6. Click **Add secret**.

> **Note:** `GITHUB_TOKEN` is automatically created and injected by GitHub Actions for every run. You do not need to add it manually.

### 2. Enable Workflow Permissions

By default, GitHub Actions tokens have read-only permissions in new repositories. Enable write access:

1. Go to **Settings** > **Actions** > **General**.
2. Scroll to **Workflow permissions**.
3. Select **Read and write permissions**.
4. Check **Allow GitHub Actions to create and approve pull requests**.
5. Click **Save**.

### 3. Local Testing

To test scripts locally before pushing:

```bash
# Clone the repository
git clone https://github.com/your-username/opensource-agents.git
cd opensource-agents

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your actual OPENAI_API_KEY and GITHUB_TOKEN
```

Run a syntax check across all scripts:

```bash
python -m py_compile scripts/*.py
```

---

## ⚙️ Configuration & Customization

- **Model**: All scripts use `gpt-4o-mini` for fast response times and low cost. You can change `model="gpt-4o-mini"` to `gpt-4o` in `scripts/*.py` if needed.
- **Prompts**: Edit prompts in `.github/prompts/` to fit your project's coding standards, tone of voice, or specific issue labels.
- **Duplicate Threshold**: In `scripts/issue_triage.py`, adjust `DUPLICATE_THRESHOLD = 0.90` (0.0 to 1.0) to control how aggressively similar issues are flagged.
- **Target Languages**: In `scripts/community_translate.py`, modify `TARGET_LANGUAGES` to add or remove language codes.

---

## 📄 License

MIT License. Free to use and modify for any open-source or commercial project.