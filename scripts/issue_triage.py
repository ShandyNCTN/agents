"""
Issue Triage Agent
------------------
Triggered by GitHub Actions when a new issue is opened.
- Labels the issue (bug, enhancement, documentation, question, duplicate)
- Checks for duplicates via embedding similarity against recent open issues
- Replies with FAQ/docs links for question-type issues
"""

import json
import logging
import math
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
# Config from environment
# ---------------------------------------------------------------------------
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-3.8-flash")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "gemini-embedding-001")
REPO = os.environ["REPO_FULL_NAME"]          # e.g. "owner/repo"
ISSUE_NUMBER = int(os.environ["ISSUE_NUMBER"])
ISSUE_TITLE = os.environ.get("ISSUE_TITLE", "")
ISSUE_BODY = os.environ.get("ISSUE_BODY", "") or ""
ISSUE_AUTHOR = os.environ.get("ISSUE_AUTHOR", "")

GH_API = "https://api.github.com"
GH_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

DUPLICATE_THRESHOLD = 0.90  # cosine similarity cutoff
MAX_RECENT_ISSUES = 30      # issues to scan for duplicates

# Label definitions available in the repo (create them manually or via API)
VALID_LABELS = {"bug", "enhancement", "documentation", "question", "duplicate"}

# Docs / FAQ links – customise per project
FAQ_LINKS = """
**Useful links before you wait for a reply:**
- 📖 [Documentation](../../wiki)
- ❓ [FAQ](../../wiki/FAQ)
- 💬 [Discussions](../../discussions)
- 🔍 [Search existing issues](../../issues?q=is%3Aissue)
"""

openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL if OPENAI_BASE_URL else None,
)


# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------

def gh_get(path: str, params: dict | None = None) -> dict | list:
    url = f"{GH_API}{path}"
    resp = requests.get(url, headers=GH_HEADERS, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def gh_post(path: str, body: dict) -> dict:
    url = f"{GH_API}{path}"
    resp = requests.post(url, headers=GH_HEADERS, json=body, timeout=30)
    resp.raise_for_status()
    return resp.json()


def gh_patch(path: str, body: dict) -> dict:
    url = f"{GH_API}{path}"
    resp = requests.patch(url, headers=GH_HEADERS, json=body, timeout=30)
    resp.raise_for_status()
    return resp.json()


def ensure_label_exists(label: str) -> None:
    """Create the label in the repo if it doesn't exist yet."""
    colour_map = {
        "bug": "d73a4a",
        "enhancement": "a2eeef",
        "documentation": "0075ca",
        "question": "e4e669",
        "duplicate": "cfd3d7",
    }
    try:
        gh_get(f"/repos/{REPO}/labels/{label}")
    except requests.HTTPError as exc:
        if exc.response.status_code == 404:
            gh_post(
                f"/repos/{REPO}/labels",
                {"name": label, "color": colour_map.get(label, "ededed")},
            )
            log.info("Created label: %s", label)
        else:
            raise


def add_labels(labels: list[str]) -> None:
    for label in labels:
        ensure_label_exists(label)
    gh_post(
        f"/repos/{REPO}/issues/{ISSUE_NUMBER}/labels",
        {"labels": labels},
    )
    log.info("Applied labels: %s", labels)


def post_comment(body: str) -> None:
    gh_post(
        f"/repos/{REPO}/issues/{ISSUE_NUMBER}/comments",
        {"body": body},
    )
    log.info("Posted comment on issue #%d", ISSUE_NUMBER)


def close_as_duplicate(original_number: int) -> None:
    gh_patch(
        f"/repos/{REPO}/issues/{ISSUE_NUMBER}",
        {"state": "closed", "state_reason": "not_planned"},
    )
    log.info("Closed issue #%d as duplicate of #%d", ISSUE_NUMBER, original_number)


# ---------------------------------------------------------------------------
# OpenAI helpers
# ---------------------------------------------------------------------------

def load_system_prompt() -> str:
    prompt_path = ".github/prompts/issue_triage.txt"
    if os.path.exists(prompt_path):
        with open(prompt_path) as f:
            return f.read()
    # Fallback inline prompt
    return (
        "You are an expert open-source project maintainer. "
        "Classify GitHub issues and help contributors efficiently."
    )


def classify_issue(title: str, body: str) -> dict:
    """
    Ask GPT to classify the issue.
    Returns {"label": str, "reason": str, "faq_reply": str | None}
    """
    system = load_system_prompt()
    user_msg = f"""Classify the following GitHub issue and respond with valid JSON only.

Issue title: {title}
Issue body:
{body[:3000]}

Respond with this exact JSON structure (no markdown fences):
{{
  "label": "<one of: bug, enhancement, documentation, question>",
  "reason": "<one sentence explaining your classification>",
  "faq_reply": "<optional friendly reply if this is a question, else null>"
}}"""

    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
        max_tokens=512,
    )

    raw = response.choices[0].message.content.strip()
    # Strip potential markdown code fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


def get_embedding(text: str) -> list[float]:
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text[:8000],
    )
    return response.data[0].embedding


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------

def find_duplicate() -> dict | None:
    """
    Fetch recent open issues, embed them, compare with current issue.
    Returns the most similar issue dict if similarity >= threshold, else None.
    """
    log.info("Fetching recent issues for duplicate check...")
    issues = gh_get(
        f"/repos/{REPO}/issues",
        params={"state": "open", "per_page": MAX_RECENT_ISSUES, "sort": "created", "direction": "desc"},
    )

    current_text = f"{ISSUE_TITLE}\n{ISSUE_BODY}"
    current_embedding = get_embedding(current_text)

    best_score = 0.0
    best_issue = None

    for issue in issues:
        # Skip the current issue itself and pull requests
        if issue["number"] == ISSUE_NUMBER or "pull_request" in issue:
            continue

        candidate_text = f"{issue['title']}\n{issue.get('body') or ''}"
        candidate_embedding = get_embedding(candidate_text)
        score = cosine_similarity(current_embedding, candidate_embedding)
        log.info("Issue #%d similarity: %.3f", issue["number"], score)

        if score > best_score:
            best_score = score
            best_issue = issue

    if best_score >= DUPLICATE_THRESHOLD and best_issue:
        log.info("Duplicate found: #%d (score=%.3f)", best_issue["number"], best_score)
        return best_issue

    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    log.info("Triaging issue #%d: %s", ISSUE_NUMBER, ISSUE_TITLE)

    # 1. Classify via GPT
    classification = classify_issue(ISSUE_TITLE, ISSUE_BODY)
    label = classification.get("label", "question")
    reason = classification.get("reason", "")
    faq_reply = classification.get("faq_reply")

    if label not in VALID_LABELS:
        label = "question"

    log.info("Classification: label=%s, reason=%s", label, reason)

    # 2. Duplicate check (skip if already classified as duplicate)
    duplicate_issue = find_duplicate()

    if duplicate_issue:
        label = "duplicate"
        add_labels(["duplicate"])
        comment = (
            f"👋 @{ISSUE_AUTHOR}, this issue appears to be a duplicate of "
            f"#{duplicate_issue['number']}: **{duplicate_issue['title']}**.\n\n"
            f"Please continue the discussion there. This issue will be closed. "
            f"If you believe this is NOT a duplicate, please reopen and explain the difference."
        )
        post_comment(comment)
        close_as_duplicate(duplicate_issue["number"])
        return

    # 3. Apply label
    add_labels([label])

    # 4. Post reply for questions
    if label == "question" and faq_reply:
        comment = (
            f"👋 @{ISSUE_AUTHOR}, thanks for reaching out!\n\n"
            f"{faq_reply}\n\n"
            f"{FAQ_LINKS}\n\n"
            f"*If this doesn't answer your question, a maintainer will follow up soon.*"
        )
        post_comment(comment)
    elif label == "bug":
        comment = (
            f"🐛 Thanks for the bug report, @{ISSUE_AUTHOR}! "
            f"We've labelled this as a **bug** and will investigate.\n\n"
            f"To help us reproduce faster, please ensure you've included:\n"
            f"- Steps to reproduce\n"
            f"- Expected vs actual behaviour\n"
            f"- Environment details (OS, version, etc.)"
        )
        post_comment(comment)
    elif label == "enhancement":
        comment = (
            f"✨ Thanks for the feature request, @{ISSUE_AUTHOR}! "
            f"Labelled as **enhancement** for review by the team."
        )
        post_comment(comment)

    log.info("Triage complete for issue #%d", ISSUE_NUMBER)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.exception("Triage agent failed: %s", exc)
        sys.exit(1)
