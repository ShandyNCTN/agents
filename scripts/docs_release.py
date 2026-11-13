"""
Docs & Release Notes Agent
--------------------------
Handles two triggers:

1. push to main:
   - Analyzes commits since last tag
   - Checks if README / docs need updating
   - Creates a PR with suggested doc updates if needed

2. release published:
   - Generates changelog from merged PRs since last release
   - Formats as markdown and updates CHANGELOG.md
   - Updates the GitHub release body
"""

import logging
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

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
EVENT_NAME = os.environ.get("EVENT_NAME", "push")
REF_NAME = os.environ.get("REF_NAME", "main")
RELEASE_TAG = os.environ.get("RELEASE_TAG", "")
RELEASE_ID = os.environ.get("RELEASE_ID", "")
RELEASE_NAME = os.environ.get("RELEASE_NAME", "")

GH_API = "https://api.github.com"
GH_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

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


def gh_patch(path: str, body: dict) -> dict:
    resp = requests.patch(f"{GH_API}{path}", headers=GH_HEADERS, json=body, timeout=30)
    resp.raise_for_status()
    return resp.json()


def git(*args) -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Shared: load system prompt
# ---------------------------------------------------------------------------

def load_system_prompt(name: str) -> str:
    path = f".github/prompts/{name}.txt"
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return "You are a technical writer for an open-source project."


# ---------------------------------------------------------------------------
# Push handler: docs freshness check
# ---------------------------------------------------------------------------

def get_commits_since_last_tag() -> list[dict]:
    """Return commit subjects since the last git tag (or last 20 commits)."""
    try:
        last_tag = git("describe", "--tags", "--abbrev=0")
        log.info("Last tag: %s", last_tag)
        log_output = git("log", f"{last_tag}..HEAD", "--pretty=format:%H|%s|%an")
    except subprocess.CalledProcessError:
        # No tags yet — use last 20 commits
        log.info("No tags found, using last 20 commits")
        log_output = git("log", "-20", "--pretty=format:%H|%s|%an")

    commits = []
    for line in log_output.splitlines():
        if "|" in line:
            parts = line.split("|", 2)
            commits.append({"sha": parts[0], "subject": parts[1], "author": parts[2]})
    return commits


def check_docs_need_update(commits: list[dict]) -> dict:
    """Ask GPT if commit messages suggest docs or migration guides need updating."""
    if not commits:
        return {"needs_update": False, "reason": "No commits", "suggested_changes": ""}

    commit_text = "\n".join(f"- {c['subject']} (by {c['author']})" for c in commits)
    system = load_system_prompt("docs_release")

    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": (
                    f"These commits were pushed to main:\n{commit_text}\n\n"
                    "Determine if documentation or README needs updating, especially if any public API changed or broke. "
                    "Respond with JSON only:\n"
                    '{"needs_update": true|false, "reason": "...", "suggested_changes": "...", "has_breaking_changes": true|false}'
                ),
            },
        ],
        temperature=0.3,
        max_tokens=600,
    )

    import json
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


def create_docs_pr(suggested_changes: str, has_breaking_changes: bool = False) -> None:
    """Create a GitHub issue flagging doc needs, highlighting breaking changes and migration guide."""
    breaking_notice = ""
    if has_breaking_changes:
        breaking_notice = (
            "### ⚠️ Semantic Breaking Changes Detected!\n"
            "Recent commits appear to modify or remove existing public interfaces. "
            "Please draft a **Breaking Changes & Migration Guide** in README.md / docs.\n\n"
        )

    body = (
        "## 📝 Documentation Update Suggested\n\n"
        f"{breaking_notice}"
        "The AI docs agent detected that recent commits may require documentation updates.\n\n"
        f"**Suggested changes:**\n{suggested_changes}\n\n"
        "Please review and update the relevant documentation files.\n\n"
        "*Auto-generated by the Docs & Release Notes Agent*"
    )
    title = (
        "docs: update documentation & migration guide for breaking changes"
        if has_breaking_changes
        else "docs: update documentation after recent changes"
    )
    gh_post(
        f"/repos/{REPO}/issues",
        {
            "title": title,
            "body": body,
            "labels": ["documentation"],
        },
    )
    log.info("Created documentation update issue (has_breaking_changes=%s)", has_breaking_changes)


def handle_push() -> None:
    log.info("Handling push to %s", REF_NAME)
    commits = get_commits_since_last_tag()
    log.info("Found %d commits since last tag", len(commits))

    if not commits:
        log.info("No new commits — nothing to do")
        return

    result = check_docs_need_update(commits)
    log.info("Docs need update: %s — %s", result.get("needs_update"), result.get("reason"))

    if result.get("needs_update") and result.get("suggested_changes"):
        create_docs_pr(result["suggested_changes"], result.get("has_breaking_changes", False))


# ---------------------------------------------------------------------------
# Release handler: changelog generation
# ---------------------------------------------------------------------------

def get_tags() -> list[str]:
    """Return list of tag names, newest first."""
    tags = gh_get(f"/repos/{REPO}/tags", params={"per_page": 10})
    return [t["name"] for t in tags]


def get_merged_prs_since_tag(prev_tag: str | None) -> list[dict]:
    """
    Return merged PRs. If prev_tag is known, filter by merge date after that tag's commit date.
    """
    prs = []
    page = 1
    cutoff_date = None

    if prev_tag:
        try:
            tag_info = gh_get(f"/repos/{REPO}/git/refs/tags/{prev_tag}")
            sha = tag_info.get("object", {}).get("sha", "")
            if sha:
                commit = gh_get(f"/repos/{REPO}/git/commits/{sha}")
                cutoff_date = commit.get("committer", {}).get("date")
                log.info("Cutoff date from tag %s: %s", prev_tag, cutoff_date)
        except Exception:
            log.warning("Could not resolve tag %s date", prev_tag)

    while True:
        page_prs = gh_get(
            f"/repos/{REPO}/pulls",
            params={"state": "closed", "sort": "updated", "direction": "desc", "per_page": 50, "page": page},
        )
        if not page_prs:
            break

        for pr in page_prs:
            if not pr.get("merged_at"):
                continue
            if cutoff_date and pr["merged_at"] <= cutoff_date:
                break
            prs.append(pr)

        if len(page_prs) < 50:
            break
        page += 1

    log.info("Found %d merged PRs since %s", len(prs), prev_tag)
    return prs


def generate_changelog(prs: list[dict], tag: str, release_name: str) -> str:
    """Ask GPT to format PRs into a structured changelog with semantic breaking changes & migration guide."""
    if not prs:
        pr_summary = "No merged pull requests found for this release."
    else:
        pr_items = []
        for pr in prs[:50]:
            body_snippet = (pr.get("body") or "").strip().replace("\n", " ")[:150]
            desc = f"- PR #{pr['number']}: {pr['title']} (by @{pr['user']['login']})"
            if body_snippet:
                desc += f" — details: {body_snippet}"
            pr_items.append(desc)
        pr_summary = "\n".join(pr_items)

    system = load_system_prompt("docs_release")
    prompt = f"""Generate a release changelog for release {tag} ({release_name}) from merged pull requests:

{pr_summary}

Requirements:
1. Detect any semantic breaking changes (deleted/renamed public APIs, altered method signatures, removed flags or env vars).
2. If breaking changes exist, lead with a prominent dedicated section:
### ⚠️ Breaking Changes & Migration Guide
- Describe Old API -> New API
- Provide actionable Before/After code examples showing how callers migrate.
3. Follow with standard categories (only include sections that have items):
### 🚀 Features
### 🐛 Bug Fixes
### 📝 Documentation
### 🔧 Maintenance & Refactoring
4. Format each item as: `- Description (#PR_NUMBER) @author`
Start directly with the markdown content, no conversational preamble."""

    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=2500,
    )
    return response.choices[0].message.content.strip()


def read_changelog() -> str:
    if os.path.exists("CHANGELOG.md"):
        with open("CHANGELOG.md") as f:
            return f.read()
    return "# Changelog\n\nAll notable changes to this project will be documented here.\n\n"


def write_changelog(new_section: str, tag: str) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    existing = read_changelog()

    # Insert new section after the header
    header_end = existing.find("\n\n") + 2
    header = existing[:header_end]
    rest = existing[header_end:]

    new_content = (
        f"{header}"
        f"## [{tag}] - {today}\n\n"
        f"{new_section}\n\n"
        f"{rest}"
    )

    with open("CHANGELOG.md", "w") as f:
        f.write(new_content)
    log.info("Updated CHANGELOG.md")


def update_release_body(release_id: str, body: str) -> None:
    gh_patch(
        f"/repos/{REPO}/releases/{release_id}",
        {"body": body},
    )
    log.info("Updated release body for release ID %s", release_id)


def commit_and_push_changelog(tag: str) -> None:
    """
    Commit CHANGELOG.md update and push directly to main.
    This runs inside the workflow checkout, so git is already configured.
    """
    try:
        git("config", "user.email", "github-actions[bot]@users.noreply.github.com")
        git("config", "user.name", "github-actions[bot]")

        # Set remote URL with token for push
        remote_url = f"https://x-access-token:{GITHUB_TOKEN}@github.com/{REPO}.git"
        git("remote", "set-url", "origin", remote_url)

        git("add", "CHANGELOG.md")
        git("commit", "-m", f"docs: update CHANGELOG.md for {tag} [skip ci]")
        git("push", "origin", "HEAD:main")
        log.info("Pushed CHANGELOG.md update to main")
    except subprocess.CalledProcessError as e:
        log.warning("Could not commit changelog: %s", e)


def handle_release() -> None:
    log.info("Handling release: tag=%s, id=%s", RELEASE_TAG, RELEASE_ID)

    tags = get_tags()
    # Find previous tag (the one before RELEASE_TAG)
    try:
        current_idx = tags.index(RELEASE_TAG)
        prev_tag = tags[current_idx + 1] if current_idx + 1 < len(tags) else None
    except ValueError:
        prev_tag = tags[1] if len(tags) > 1 else None

    log.info("Previous tag: %s", prev_tag)

    prs = get_merged_prs_since_tag(prev_tag)
    changelog = generate_changelog(prs, RELEASE_TAG, RELEASE_NAME)

    log.info("Generated changelog:\n%s", changelog)

    # Update CHANGELOG.md
    write_changelog(changelog, RELEASE_TAG)
    commit_and_push_changelog(RELEASE_TAG)

    # Update GitHub release body
    if RELEASE_ID:
        full_body = f"## What's Changed\n\n{changelog}\n\n**Full Changelog:** https://github.com/{REPO}/compare/{prev_tag or ''}...{RELEASE_TAG}"
        update_release_body(RELEASE_ID, full_body)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if EVENT_NAME == "release":
        handle_release()
    else:
        handle_push()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.exception("Docs/release agent failed: %s", exc)
        sys.exit(1)
