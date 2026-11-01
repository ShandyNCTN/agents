"""
Community & Translation Agent
------------------------------
Handles three responsibilities:

1. Translating docs (README.md, CONTRIBUTING.md) to id, zh, ja, es, ar:
   - Triggered on schedule (weekly), manual dispatch, or 'translate' label on issue
   - Saves translations under docs/translations/{lang}/
   - Pushes updates or creates PR

2. Welcoming first-time contributors on their first PR:
   - Checks contributor history via GitHub API
   - Posts a friendly, warm welcome message with helpful links
"""

import json
import logging
import os
import subprocess
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
EVENT_NAME = os.environ.get("EVENT_NAME", "")
LABEL_NAME = os.environ.get("LABEL_NAME", "")
ISSUE_NUMBER = os.environ.get("ISSUE_NUMBER", "")
PR_NUMBER = os.environ.get("PR_NUMBER", "")
PR_AUTHOR = os.environ.get("PR_AUTHOR", "")

GH_API = "https://api.github.com"
GH_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Supported target languages: code -> display name
TARGET_LANGUAGES = {
    "id": "Indonesian (Bahasa Indonesia)",
    "zh": "Simplified Chinese (简体中文)",
    "ja": "Japanese (日本語)",
    "es": "Spanish (Español)",
    "ar": "Arabic (العربية)",
}

# Docs files to translate
DOCS_TO_TRANSLATE = ["README.md", "CONTRIBUTING.md"]

openai_client = OpenAI(api_key=OPENAI_API_KEY)


# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------

def gh_get(path: str, params: dict | None = None) -> dict | list:
    resp = requests.get(f"{GH_API}{path}", headers=GH_HEADERS, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def gh_post(path: str, body: dict) -> dict:
    resp = requests.post(f"{GH_API}{path}", headers=GH_HEADERS, json=body, timeout=30)
    resp.raise_for_status()
    return resp.json()


def git(*args) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# First-time contributor welcome
# ---------------------------------------------------------------------------

def is_first_time_contributor(username: str) -> bool:
    """Check if the user has any previously merged PRs in this repo."""
    try:
        data = gh_get(
            f"/search/issues",
            params={
                "q": f"repo:{REPO} is:pr is:merged author:{username}",
                "per_page": 1,
            },
        )
        total_count = data.get("total_count", 0)
        log.info("Author %s has %d previously merged PRs", username, total_count)
        return total_count == 0
    except Exception as exc:
        log.warning("Could not check contributor history: %s. Assuming first-time.", exc)
        return True


def post_welcome_comment(pr_num: int, author: str) -> None:
    welcome_body = f"""👋 Hi @{author}! Welcome and thank you for opening your first pull request! 🎉

Here are a few quick tips to help your contribution go smoothly:
- 📖 Please ensure your code follows our [Contributing Guidelines](CONTRIBUTING.md)
- 🧪 Check that all tests pass and consider adding new tests for your changes
- 🤖 Our AI PR Reviewer will leave automated feedback shortly to help catch any early issues
- 💬 Maintainers will review your PR as soon as possible. Feel free to leave questions in this thread

Thank you for helping make this project better! 🚀"""

    gh_post(
        f"/repos/{REPO}/issues/{pr_num}/comments",
        {"body": welcome_body},
    )
    log.info("Posted welcome comment to PR #%d for @%s", pr_num, author)


def handle_pull_request() -> None:
    if not PR_NUMBER or not PR_AUTHOR:
        log.info("Missing PR context, skipping welcome")
        return

    pr_num = int(PR_NUMBER)
    if is_first_time_contributor(PR_AUTHOR):
        post_welcome_comment(pr_num, PR_AUTHOR)
    else:
        log.info("Author @%s is a returning contributor; skipping welcome comment.", PR_AUTHOR)


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------

def load_system_prompt() -> str:
    path = ".github/prompts/community_translate.txt"
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return (
        "You are an expert technical translator specializing in open-source software documentation. "
        "Produce fluent, culturally natural, and technically accurate translations."
    )


def translate_text(text: str, target_lang_name: str) -> str:
    """Translate markdown text to target language preserving formatting and code blocks."""
    system = load_system_prompt()

    user_msg = f"""Translate the following markdown document into {target_lang_name}.

Rules:
- Preserve all markdown syntax, headings, bullet points, links, and code blocks exactly
- Do NOT translate code blocks, variable names, CLI commands, file paths, or URLs
- For Arabic (ar), ensure text flow makes sense with RTL/LTR mixed technical content
- Keep the tone professional, welcoming, and natural for developers in that language
- Output ONLY the translated document, no conversational preface or postscript

Document to translate:
{text}"""

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.3,
        max_tokens=4096,
    )
    return response.choices[0].message.content.strip()


def run_translations() -> None:
    """Translate documentation files into all target languages and save them."""
    updated_files = []

    for doc_file in DOCS_TO_TRANSLATE:
        if not os.path.exists(doc_file):
            log.warning("File %s not found, skipping.", doc_file)
            continue

        with open(doc_file, encoding="utf-8") as f:
            original_content = f.read()

        for lang_code, lang_name in TARGET_LANGUAGES.items():
            log.info("Translating %s to %s (%s)...", doc_file, lang_code, lang_name)
            try:
                translated = translate_text(original_content, lang_name)

                out_dir = f"docs/translations/{lang_code}"
                os.makedirs(out_dir, exist_ok=True)
                out_path = f"{out_dir}/{doc_file}"

                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(translated)

                updated_files.append(out_path)
                log.info("Saved %s", out_path)
            except Exception as exc:
                log.error("Failed to translate %s to %s: %s", doc_file, lang_code, exc)

    if updated_files:
        commit_translations(updated_files)


def commit_translations(files: list[str]) -> None:
    """Commit updated translations directly to main."""
    try:
        git("config", "user.email", "github-actions[bot]@users.noreply.github.com")
        git("config", "user.name", "github-actions[bot]")

        remote_url = f"https://x-access-token:{GITHUB_TOKEN}@github.com/{REPO}.git"
        git("remote", "set-url", "origin", remote_url)

        for f in files:
            git("add", f)

        git("commit", "-m", "docs: update community translations [skip ci]")
        git("push", "origin", "HEAD:main")
        log.info("Pushed updated translations to main")
    except subprocess.CalledProcessError as e:
        log.warning("Could not commit translations: %s", e)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    log.info("Community & Translation Agent running (event=%s)", EVENT_NAME)

    if EVENT_NAME == "pull_request":
        handle_pull_request()
    elif EVENT_NAME in ("schedule", "workflow_dispatch"):
        run_translations()
    elif EVENT_NAME == "issues":
        if LABEL_NAME == "translate":
            log.info("Translate label detected on issue #%s, running full translation pass", ISSUE_NUMBER)
            run_translations()
        else:
            log.info("Label '%s' is not 'translate', skipping", LABEL_NAME)
    else:
        # Default: run translations
        run_translations()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.exception("Community agent failed: %s", exc)
        sys.exit(1)
