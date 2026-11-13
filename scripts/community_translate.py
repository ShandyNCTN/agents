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
import re
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
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-3.5-flash-lite")
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

openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL if OPENAI_BASE_URL else None,
)


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
# Contributor Lint & Onboarding Mentor
# ---------------------------------------------------------------------------

CONVENTIONAL_COMMIT_REGEX = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(\([a-zA-Z0-9_\-\./\s]+\))?(!)?:\s.+"
)


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


def get_contributor_profile(username: str) -> dict:
    """Fetch contributor public profile info to infer location and language preference."""
    try:
        user_data = gh_get(f"/users/{username}")
        if isinstance(user_data, dict):
            return {
                "name": user_data.get("name"),
                "location": user_data.get("location"),
                "bio": user_data.get("bio"),
                "company": user_data.get("company"),
            }
    except Exception as exc:
        log.warning("Could not fetch user profile for %s: %s", username, exc)
    return {}


def lint_pr_commits(pr_num: int) -> dict:
    """Check if all PR commits adhere to Conventional Commits."""
    try:
        commits = gh_get(f"/repos/{REPO}/pulls/{pr_num}/commits")
        if not isinstance(commits, list):
            commits = []
    except Exception as exc:
        log.warning("Could not fetch commits for PR #%d: %s", pr_num, exc)
        commits = []

    non_conforming = []
    for c in commits:
        msg = c.get("commit", {}).get("message", "")
        subject = msg.splitlines()[0] if msg else ""
        if not CONVENTIONAL_COMMIT_REGEX.match(subject):
            non_conforming.append(subject)

    return {
        "total": len(commits),
        "non_conforming": non_conforming,
        "is_valid": len(non_conforming) == 0,
    }


def check_branch_sync(pr: dict) -> dict:
    """Check if the PR branch is up to date with base."""
    if not isinstance(pr, dict):
        return {"behind_by": 0, "ahead_by": 0, "base_ref": "main"}

    base_ref = pr.get("base", {}).get("ref", "main")
    head_sha = pr.get("head", {}).get("sha", "")
    if not head_sha:
        return {"behind_by": 0, "ahead_by": 0, "base_ref": base_ref}

    try:
        compare_data = gh_get(f"/repos/{REPO}/compare/{base_ref}...{head_sha}")
        behind_by = compare_data.get("behind_by", 0) if isinstance(compare_data, dict) else 0
        ahead_by = compare_data.get("ahead_by", 0) if isinstance(compare_data, dict) else 0
        return {"behind_by": behind_by, "ahead_by": ahead_by, "base_ref": base_ref}
    except Exception as exc:
        log.warning("Could not compare branches for PR: %s", exc)
        return {"behind_by": 0, "ahead_by": 0, "base_ref": base_ref}


def generate_mentor_comment(
    author: str,
    pr_num: int,
    pr_title: str,
    pr_body: str,
    is_first_time: bool,
    profile: dict,
    commit_lint: dict,
    sync_status: dict,
) -> str:
    """Use GPT to generate an empathetic, localized onboarding mentor comment."""
    system = load_system_prompt()
    user_context = f"""Contributor: @{author}
First-time contributor: {is_first_time}
Profile Location: {profile.get('location') or 'Not specified'}
Profile Bio: {profile.get('bio') or 'Not specified'}
PR #{pr_num}: {pr_title}
PR Description: {(pr_body or '')[:500]}

Commit Hygiene:
- Total commits: {commit_lint['total']}
- Valid Conventional Commits: {commit_lint['is_valid']}
- Non-conforming commits: {commit_lint['non_conforming']}

Branch Sync Status:
- Base branch: {sync_status.get('base_ref', 'main')}
- Behind base by: {sync_status.get('behind_by', 0)} commits
"""

    prompt = f"""You are the Contributor Onboarding Mentor for this open source repository.
Review the following contributor profile and PR state:
{user_context}

Instructions:
1. Detect contributor's preferred language based on their profile location, bio, or PR description (e.g. Indonesian if location is Indonesia/Jakarta, Spanish for Spain/Latin America, Chinese for China/Taiwan, Japanese for Japan, or English as global default).
2. Write a warm, encouraging mentorship comment in their preferred language.
3. Structure:
   - Friendly greeting & thank them for opening PR #{pr_num} (celebrate enthusiastically if first-time contributor!).
   - Commit message hygiene review:
     * If all commits match Conventional Commits, praise them.
     * If any commit does not match, politely explain why Conventional Commits matter and give a clear example.
   - Branch status:
     * If behind base branch ({sync_status.get('base_ref')}), kindly explain how to update with git rebase commands.
     * If up to date, confirm it.
   - Next steps: reassuring closing note that CI and reviewers are here to help.

Output ONLY the markdown comment text (no markdown wrapping fences around the whole response)."""

    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=1500,
    )
    raw = response.choices[0].message.content or ""
    return raw.strip()


def handle_pull_request() -> None:
    if not PR_NUMBER or not PR_AUTHOR:
        log.info("Missing PR context, skipping contributor onboarding mentor")
        return

    pr_num = int(PR_NUMBER)
    first_time = is_first_time_contributor(PR_AUTHOR)
    profile = get_contributor_profile(PR_AUTHOR)

    pr_raw = {}
    try:
        pr_raw = gh_get(f"/repos/{REPO}/pulls/{pr_num}")
    except Exception as exc:
        log.warning("Could not fetch PR data for #%d: %s", pr_num, exc)

    pr_data = pr_raw if isinstance(pr_raw, dict) else {}
    pr_title = str(pr_data.get("title", ""))
    pr_body = str(pr_data.get("body", ""))

    commit_lint = lint_pr_commits(pr_num)
    sync_status = check_branch_sync(pr_data)

    log.info(
        "Mentoring @%s: first_time=%s, commit_valid=%s, behind_by=%d",
        PR_AUTHOR,
        first_time,
        commit_lint["is_valid"],
        sync_status.get("behind_by", 0),
    )

    comment_body = generate_mentor_comment(
        author=PR_AUTHOR,
        pr_num=pr_num,
        pr_title=pr_title,
        pr_body=pr_body,
        is_first_time=first_time,
        profile=profile,
        commit_lint=commit_lint,
        sync_status=sync_status,
    )

    gh_post(
        f"/repos/{REPO}/issues/{pr_num}/comments",
        {"body": comment_body},
    )
    log.info("Posted onboarding mentorship comment to PR #%d for @%s", pr_num, PR_AUTHOR)


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
        model=LLM_MODEL,
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
