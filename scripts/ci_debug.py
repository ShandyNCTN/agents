"""
CI Debugger Agent
-----------------
Triggered by GitHub Actions when any workflow finishes with conclusion 'failure'.
- Downloads failed workflow logs via GitHub API
- Sends logs to GPT-4o-mini for root cause analysis
- Posts analysis as PR comment (if PR-triggered) or creates an issue
- If diagnosis points to a simple fix (e.g. pinned dependency bump), creates a fix PR
"""

import base64
import io
import json
import logging
import os
import re
import sys
import zipfile

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
FAILED_RUN_ID = os.environ["FAILED_RUN_ID"]
FAILED_WORKFLOW_NAME = os.environ.get("FAILED_WORKFLOW_NAME", "CI")
HEAD_BRANCH = os.environ.get("HEAD_BRANCH", "main")
HEAD_SHA = os.environ.get("HEAD_SHA", "")
EVENT_TYPE = os.environ.get("EVENT_TYPE", "")
PULL_REQUESTS_RAW = os.environ.get("PULL_REQUESTS", "[]")

GH_API = "https://api.github.com"
GH_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

MAX_LOG_CHARS = 10000

openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL if OPENAI_BASE_URL else None,
)


# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------

def gh_get(path: str, params: dict | None = None, stream: bool = False) -> requests.Response:
    url = f"{GH_API}{path}"
    resp = requests.get(url, headers=GH_HEADERS, params=params, stream=stream, timeout=60)
    resp.raise_for_status()
    return resp


def gh_post(path: str, body: dict) -> dict:
    url = f"{GH_API}{path}"
    resp = requests.post(url, headers=GH_HEADERS, json=body, timeout=30)
    resp.raise_for_status()
    return resp.json()


def gh_put(path: str, body: dict) -> dict:
    url = f"{GH_API}{path}"
    resp = requests.put(url, headers=GH_HEADERS, json=body, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Log extraction
# ---------------------------------------------------------------------------

def get_failed_step_logs() -> str:
    """
    Download workflow logs zip, find failed steps, extract relevant error lines.
    """
    log.info("Downloading logs for run %s...", FAILED_RUN_ID)
    try:
        resp = gh_get(f"/repos/{REPO}/actions/runs/{FAILED_RUN_ID}/logs", stream=True)
    except requests.HTTPError as e:
        log.warning("Could not download zip logs: %s. Falling back to jobs API.", e)
        return get_logs_from_jobs_api()

    log_buffer = io.BytesIO(resp.content)
    all_logs = []

    try:
        with zipfile.ZipFile(log_buffer) as z:
            for filename in z.namelist():
                # Look for files with errors or failed job names
                text = z.read(filename).decode("utf-8", errors="replace")
                # Look for typical error markers
                if any(kw in text.lower() for kw in ["error:", "failed", "fatal:", "exception", "traceback"]):
                    all_logs.append(f"--- File: {filename} ---\n{text}")
    except zipfile.BadZipFile:
        log.warning("Downloaded log was not a valid zip")
        return get_logs_from_jobs_api()

    combined = "\n\n".join(all_logs)
    if not combined.strip():
        # Fallback to reading all files up to limit
        log.info("No explicit error markers found in log files, taking tail of all logs")
        with zipfile.ZipFile(log_buffer) as z:
            combined = "\n\n".join(
                f"--- {fn} ---\n{z.read(fn).decode('utf-8', errors='replace')[-2000:]}"
                for fn in z.namelist()[:5]
            )

    return extract_error_tail(combined)


def get_logs_from_jobs_api() -> str:
    """Fallback: fetch jobs for run, find the failed one, return its steps."""
    data = gh_get(f"/repos/{REPO}/actions/runs/{FAILED_RUN_ID}/jobs").json()
    failed_jobs = [j for j in data.get("jobs", []) if j.get("conclusion") == "failure"]
    if not failed_jobs:
        return "No failed jobs identified."

    job = failed_jobs[0]
    failed_steps = [s for s in job.get("steps", []) if s.get("conclusion") == "failure"]
    step_names = ", ".join(s["name"] for s in failed_steps)
    return f"Job '{job['name']}' failed at step(s): {step_names}"


def extract_error_tail(log_text: str) -> str:
    """Extract error context lines, cap at MAX_LOG_CHARS."""
    # Find lines that look like errors and grab context around them
    lines = log_text.splitlines()
    error_indices = [
        i for i, line in enumerate(lines)
        if any(kw in line.lower() for kw in ["error:", "fatal:", "fail", "exception:", "traceback"])
    ]

    if not error_indices:
        # Just take the last MAX_LOG_CHARS characters
        return log_text[-MAX_LOG_CHARS:]

    # Collect unique lines around errors (up to 10 lines before, 20 after)
    keep_indices = set()
    for idx in error_indices:
        start = max(0, idx - 10)
        end = min(len(lines), idx + 20)
        keep_indices.update(range(start, end))

    extracted = "\n".join(lines[i] for i in sorted(keep_indices))
    return extracted[:MAX_LOG_CHARS]


# ---------------------------------------------------------------------------
# GPT analysis
# ---------------------------------------------------------------------------

def load_system_prompt() -> str:
    path = ".github/prompts/ci_debug.txt"
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return "You are an expert CI/CD engineer diagnosing build and test failures."


def analyze_failure(logs: str) -> dict:
    """
    Send error logs to GPT-4o-mini.
    Returns:
    {
      "root_cause": str,
      "category": str,
      "suggested_fix": str,
      "can_auto_fix": bool,
      "fix_file": str | None,
      "fix_content": str | None,
      "summary": str
    }
    """
    system = load_system_prompt()
    user_msg = f"""A GitHub Actions workflow failed.

Workflow name: {FAILED_WORKFLOW_NAME}
Run ID: {FAILED_RUN_ID}
Branch: {HEAD_BRANCH}

Error Logs:
```
{logs}
```

Diagnose this failure and respond with valid JSON only (no markdown fences):
{{
  "summary": "<1-2 sentence overview of what failed>",
  "category": "<one of: dependency|syntax|test_failure|lint|env_or_secret|timeout|other>",
  "root_cause": "<detailed explanation of the root cause>",
  "suggested_fix": "<actionable step-by-step instructions to fix>",
  "can_auto_fix": true|false,
  "fix_file": "<relative path in repo or null>",
  "fix_content": "<entire file content with fix applied or null>",
  "fix_commit_message": "<conventional commit message or null>",
  "fix_pr_body": "<markdown explanation for PR body or null>"
}}

Set can_auto_fix to true whenever the failure can be resolved with a concrete file change (e.g. fixing a typo, updating requirements, fixing a syntax error, adjusting configuration, fixing an assertion). Provide the complete updated file in fix_content."""

    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
        max_tokens=2500,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Post diagnosis
# ---------------------------------------------------------------------------

def format_diagnosis(analysis: dict, fix_pr: dict | None = None) -> str:
    category_icons = {
        "dependency": "📦",
        "syntax": "⚠️",
        "test_failure": "🧪",
        "lint": "🧹",
        "env_or_secret": "🔑",
        "timeout": "⏱️",
        "other": "🔍",
    }
    icon = category_icons.get(analysis.get("category", "other"), "🔍")

    fix_pr_section = ""
    if fix_pr and fix_pr.get("html_url"):
        pr_url = fix_pr["html_url"]
        pr_num = fix_pr.get("number")
        fix_pr_section = f"""### 🛠️ Real Auto-Heal Pull Request
An automated patch was generated, committed, and submitted to fix this failure:
👉 **[PR #{pr_num}: {fix_pr.get('title', 'Auto-Heal PR')}]({pr_url})**
"""

    return f"""## 🚨 CI Failure Diagnosis

**Workflow:** `{FAILED_WORKFLOW_NAME}` | **Run:** [#{FAILED_RUN_ID}](https://github.com/{REPO}/actions/runs/{FAILED_RUN_ID})
**Category:** {icon} `{analysis.get('category', 'unknown')}`

### Summary
{analysis.get('summary', 'Workflow failed.')}

### Root Cause
{analysis.get('root_cause', 'Unable to determine exact cause.')}

### Suggested Fix
{analysis.get('suggested_fix', 'Inspect the full logs linked above.')}

{fix_pr_section}---
*Diagnosed automatically by [CI Debugger Agent](../../.github/workflows/ci-debug.yml)*"""


def post_results(analysis: dict, fix_pr: dict | None = None) -> None:
    body = format_diagnosis(analysis, fix_pr)

    # Check if this run belongs to a PR
    try:
        prs = json.loads(PULL_REQUESTS_RAW)
    except (json.JSONDecodeError, TypeError):
        prs = []

    if prs:
        # Post comment to the PR
        pr_number = prs[0]["number"]
        log.info("Posting diagnosis to PR #%d", pr_number)
        gh_post(f"/repos/{REPO}/issues/{pr_number}/comments", {"body": body})
    else:
        # Not a PR (e.g. push to main, schedule) -> create an issue
        log.info("Posting diagnosis as new issue")
        gh_post(
            f"/repos/{REPO}/issues",
            {
                "title": f"CI Failure: `{FAILED_WORKFLOW_NAME}` on `{HEAD_BRANCH}`",
                "body": body,
                "labels": ["bug"],
            },
        )


# ---------------------------------------------------------------------------
# Auto-fix PR
# ---------------------------------------------------------------------------

def try_create_fix_pr(analysis: dict) -> dict | None:
    """Create a real branch, commit targeted fix, and open PR if GPT generated an auto-fix."""
    if not analysis.get("can_auto_fix"):
        return None

    fix_file = analysis.get("fix_file")
    fix_content = analysis.get("fix_content")
    if not fix_file or not fix_content:
        log.info("Auto-fix flagged but missing fix_file or fix_content")
        return None

    log.info("Attempting auto-heal branch and PR creation for %s", fix_file)
    branch_name = f"auto-fix/ci-run-{FAILED_RUN_ID}"

    # 1. Resolve base commit SHA
    base_sha = HEAD_SHA
    if not base_sha:
        try:
            ref_resp = gh_get(f"/repos/{REPO}/git/ref/heads/{HEAD_BRANCH}").json()
            base_sha = ref_resp["object"]["sha"]
        except Exception:
            try:
                repo_info = gh_get(f"/repos/{REPO}").json()
                default_branch = repo_info.get("default_branch", "main")
                ref_resp = gh_get(f"/repos/{REPO}/git/ref/heads/{default_branch}").json()
                base_sha = ref_resp["object"]["sha"]
            except Exception as e:
                log.error("Could not determine base SHA for branch creation: %s", e)
                return None

    # 2. Create git branch
    try:
        gh_post(
            f"/repos/{REPO}/git/refs",
            {"ref": f"refs/heads/{branch_name}", "sha": base_sha},
        )
        log.info("Created branch %s at %s", branch_name, base_sha[:7])
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 422:
            log.info("Branch %s already exists, reusing branch", branch_name)
        else:
            log.error("Failed to create branch %s: %s", branch_name, e)
            return None

    # 3. Fetch existing file SHA if file already exists on this branch
    existing_sha = None
    try:
        file_info = gh_get(f"/repos/{REPO}/contents/{fix_file}", params={"ref": branch_name}).json()
        existing_sha = file_info.get("sha")
    except Exception:
        log.info("Target file %s does not exist on branch %s; creating new file", fix_file, branch_name)

    # 4. Commit updated content
    commit_msg = analysis.get("fix_commit_message") or f"fix(ci): auto-heal workflow failure in run #{FAILED_RUN_ID}"
    b64_content = base64.b64encode(fix_content.encode("utf-8")).decode("ascii")

    put_body = {
        "message": commit_msg,
        "content": b64_content,
        "branch": branch_name,
    }
    if existing_sha:
        put_body["sha"] = existing_sha

    try:
        gh_put(f"/repos/{REPO}/contents/{fix_file}", put_body)
        log.info("Committed auto-fix to %s on branch %s", fix_file, branch_name)
    except Exception as e:
        log.error("Failed to commit auto-fix to %s: %s", fix_file, e)
        return None

    # 5. Open Pull Request
    pr_title = f"fix(ci): auto-heal workflow failure in run #{FAILED_RUN_ID}"
    pr_body = analysis.get("fix_pr_body")
    if not pr_body:
        pr_body = (
            f"## 🤖 Automated CI Auto-Heal Fix\n\n"
            f"This Pull Request was automatically generated by the **CI Debugger Agent** "
            f"to resolve a build failure in workflow `{FAILED_WORKFLOW_NAME}` (Run [#{FAILED_RUN_ID}](https://github.com/{REPO}/actions/runs/{FAILED_RUN_ID})).\n\n"
            f"### Root Cause\n{analysis.get('root_cause', 'Unknown')}\n\n"
            f"### Fix Summary\n{analysis.get('suggested_fix', 'Applied automated fix.')}\n\n"
            f"**Modified File:** `{fix_file}`\n\n"
            f"---\n*Please review and merge once CI tests pass.*"
        )

    try:
        pr_resp = gh_post(
            f"/repos/{REPO}/pulls",
            {
                "title": pr_title,
                "head": branch_name,
                "base": HEAD_BRANCH,
                "body": pr_body,
            },
        )
        log.info("Opened auto-heal PR #%s: %s", pr_resp.get("number"), pr_resp.get("html_url"))
        return pr_resp
    except requests.HTTPError as e:
        log.error("Failed to open auto-heal PR: %s", e)
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    log.info("Investigating failure for run %s (%s)", FAILED_RUN_ID, FAILED_WORKFLOW_NAME)

    logs = get_failed_step_logs()
    if not logs.strip():
        log.warning("No logs could be retrieved. Exiting.")
        return

    analysis = analyze_failure(logs)
    log.info("Analysis complete: category=%s", analysis.get("category"))

    fix_pr = try_create_fix_pr(analysis)
    post_results(analysis, fix_pr)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.exception("CI debugger agent failed: %s", exc)
        sys.exit(1)
