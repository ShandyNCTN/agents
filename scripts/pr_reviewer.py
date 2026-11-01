"""
PR Reviewer Agent
-----------------
Triggered by GitHub Actions on PR open/synchronize.
- Fetches the PR diff via GitHub API
- Sends diff to GPT-4o-mini for review (bugs, style, security, missing tests)
- Posts a consolidated review comment on the PR
- Warns if no test files are included
"""

import json
import logging
import os
import sys

import requests
from openai import OpenAI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
REPO = os.environ["REPO_FULL_NAME"]
PR_NUMBER = int(os.environ["PR_NUMBER"])
PR_TITLE = os.environ.get("PR_TITLE", "")
PR_BODY = os.environ.get("PR_BODY", "") or ""
PR_AUTHOR = os.environ.get("PR_AUTHOR", "")
BASE_SHA = os.environ.get("BASE_SHA", "")
HEAD_SHA = os.environ.get("HEAD_SHA", "")

GH_API = "https://api.github.com"
GH_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Max diff size to send to GPT (characters). Larger diffs are truncated.
MAX_DIFF_CHARS = 12000
# File extensions considered test files
TEST_PATTERNS = {"test_", "_test.", "spec.", ".spec.", "tests/", "test/"}

openai_client = OpenAI(api_key=OPENAI_API_KEY)


# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------

def gh_get(path: str, params: dict | None = None, accept: str | None = None) -> dict | list | str:
    url = f"{GH_API}{path}"
    headers = dict(GH_HEADERS)
    if accept:
        headers["Accept"] = accept
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    # Return raw text for diff content
    if accept and "diff" in accept:
        return resp.text
    return resp.json()


def gh_post(path: str, body: dict) -> dict:
    url = f"{GH_API}{path}"
    resp = requests.post(url, headers=GH_HEADERS, json=body, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_pr_diff() -> str:
    """Fetch the unified diff for this PR."""
    diff = gh_get(
        f"/repos/{REPO}/pulls/{PR_NUMBER}",
        accept="application/vnd.github.v3.diff",
    )
    return diff if isinstance(diff, str) else ""


def get_pr_files() -> list[dict]:
    """List files changed in this PR."""
    return gh_get(
        f"/repos/{REPO}/pulls/{PR_NUMBER}/files",
        params={"per_page": 100},
    )


def post_pr_comment(body: str) -> None:
    gh_post(
        f"/repos/{REPO}/issues/{PR_NUMBER}/comments",
        {"body": body},
    )
    log.info("Posted review comment on PR #%d", PR_NUMBER)


def post_pr_review(body: str, event: str = "COMMENT") -> None:
    """
    Post a pull request review.
    event: APPROVE | REQUEST_CHANGES | COMMENT
    """
    gh_post(
        f"/repos/{REPO}/pulls/{PR_NUMBER}/reviews",
        {"body": body, "event": event},
    )
    log.info("Submitted PR review (event=%s) on PR #%d", event, PR_NUMBER)


# ---------------------------------------------------------------------------
# Test coverage check
# ---------------------------------------------------------------------------

def has_test_files(files: list[dict]) -> bool:
    """Return True if any changed file looks like a test file."""
    for f in files:
        filename = f.get("filename", "").lower()
        if any(pat in filename for pat in TEST_PATTERNS):
            return True
    return False


def has_source_changes(files: list[dict]) -> bool:
    """Return True if any .py / .js / .ts / .go etc. source file was changed."""
    source_exts = {".py", ".js", ".ts", ".go", ".java", ".rb", ".rs", ".c", ".cpp"}
    for f in files:
        filename = f.get("filename", "")
        if any(filename.endswith(ext) for ext in source_exts):
            return True
    return False


# ---------------------------------------------------------------------------
# GPT review
# ---------------------------------------------------------------------------

def load_system_prompt() -> str:
    prompt_path = ".github/prompts/pr_reviewer.txt"
    if os.path.exists(prompt_path):
        with open(prompt_path) as f:
            return f.read()
    return (
        "You are a senior software engineer conducting a thorough but constructive code review. "
        "Focus on correctness, security, maintainability, and test coverage."
    )


def review_diff(diff: str, pr_title: str, pr_body: str) -> dict:
    """
    Send diff to GPT and get structured review.
    Returns {"summary": str, "issues": list[dict], "suggestions": list[str], "verdict": str}
    """
    system = load_system_prompt()
    truncated = diff[:MAX_DIFF_CHARS]
    if len(diff) > MAX_DIFF_CHARS:
        truncated += f"\n\n[... diff truncated at {MAX_DIFF_CHARS} chars ...]"

    user_msg = f"""Review the following pull request diff.

PR Title: {pr_title}
PR Description:
{pr_body[:1000]}

Diff:
```diff
{truncated}
```

Respond with valid JSON only (no markdown fences):
{{
  "summary": "<2-3 sentence overall assessment>",
  "issues": [
    {{
      "severity": "<critical|warning|info>",
      "category": "<bug|security|style|performance|test>",
      "description": "<clear description of the issue>",
      "suggestion": "<how to fix it>"
    }}
  ],
  "suggestions": ["<general improvement suggestion>"],
  "verdict": "<approve|request_changes|comment>"
}}

Be constructive. Prefer 'comment' verdict unless there are real bugs or security issues."""

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.3,
        max_tokens=2048,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Format review as markdown
# ---------------------------------------------------------------------------

def format_review(review: dict, missing_tests: bool) -> str:
    severity_emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
    category_emoji = {"bug": "🐛", "security": "🔒", "style": "✨", "performance": "⚡", "test": "🧪"}

    lines = [
        "## 🤖 AI Code Review",
        "",
        f"**Summary:** {review.get('summary', 'No summary provided.')}",
        "",
    ]

    issues = review.get("issues", [])
    if issues:
        lines += ["### Issues Found", ""]
        for i, issue in enumerate(issues, 1):
            sev = issue.get("severity", "info")
            cat = issue.get("category", "style")
            lines += [
                f"{i}. {severity_emoji.get(sev, '⚪')} {category_emoji.get(cat, '📝')} "
                f"**[{sev.upper()} / {cat}]** {issue.get('description', '')}",
                f"   > **Suggestion:** {issue.get('suggestion', '')}",
                "",
            ]
    else:
        lines += ["### ✅ No significant issues found", ""]

    suggestions = review.get("suggestions", [])
    if suggestions:
        lines += ["### 💡 General Suggestions", ""]
        for s in suggestions:
            lines.append(f"- {s}")
        lines.append("")

    if missing_tests:
        lines += [
            "### ⚠️ Missing Tests",
            "",
            "This PR modifies source files but does not include test files. "
            "Please add or update tests to maintain coverage.",
            "",
        ]

    lines += [
        "---",
        "*Review generated by [AI PR Reviewer](../../.github/workflows/pr-reviewer.yml)*",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    log.info("Reviewing PR #%d: %s", PR_NUMBER, PR_TITLE)

    # Fetch diff and file list
    diff = get_pr_diff()
    files = get_pr_files()

    if not diff.strip():
        log.info("Empty diff — nothing to review.")
        return

    # Check test coverage
    missing_tests = has_source_changes(files) and not has_test_files(files)
    log.info("Source changes: %s, Test files included: %s", has_source_changes(files), not missing_tests)

    # GPT review
    review = review_diff(diff, PR_TITLE, PR_BODY)
    verdict = review.get("verdict", "comment").upper()

    # Format and post
    comment_body = format_review(review, missing_tests)
    post_pr_comment(comment_body)

    log.info("PR review complete. Verdict: %s", verdict)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.exception("PR reviewer agent failed: %s", exc)
        sys.exit(1)
