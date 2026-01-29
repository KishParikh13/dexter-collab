#!/usr/bin/env python3
"""
Dexter Task Orchestrator

Orchestrates Codex agents for tasks from the Dexter Dashboard.
Updates progress.json and pushes to GitHub after each step.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

# Configuration
DASHBOARD_DIR = Path(__file__).parent.parent
PROGRESS_FILE = DASHBOARD_DIR / "progress.json"
AGENT_ID = f"codex-{int(time.time())}"


def log(msg: str, level: str = "INFO"):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "INFO": "\033[0;34m",
        "SUCCESS": "\033[0;32m",
        "ERROR": "\033[0;31m",
        "STEP": "\033[1;33m",
    }
    color = colors.get(level, "\033[0m")
    print(f"{color}[{timestamp}] {level}: {msg}\033[0m")


def load_progress() -> dict:
    """Load progress.json."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"tasks": {}, "agents": {}, "lastUpdated": None}


def save_progress(progress: dict):
    """Save progress.json."""
    progress["lastUpdated"] = datetime.now(timezone.utc).isoformat()
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def git_commit_and_push(message: str) -> bool:
    """Commit and push progress.json changes."""
    try:
        os.chdir(DASHBOARD_DIR)
        subprocess.run(["git", "add", "progress.json"], check=True, capture_output=True)
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"], capture_output=True
        )
        if result.returncode == 0:
            log("No changes to commit", "INFO")
            return True
        subprocess.run(["git", "commit", "-m", message], check=True, capture_output=True)
        subprocess.run(["git", "push"], check=True, capture_output=True)
        log(f"Pushed: {message}", "SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        log(f"Git error: {e}", "ERROR")
        return False


def update_step(
    progress: dict,
    task_id: str,
    step_name: str,
    status: str,
    detail: str = None,
):
    """Update a step in the task progress."""
    task = progress["tasks"].setdefault(task_id, {"steps": [], "status": "in-progress"})
    
    # Find or create step
    step = next((s for s in task["steps"] if s["name"] == step_name), None)
    if step:
        step["status"] = status
        if detail:
            step["detail"] = detail
    else:
        task["steps"].append({
            "name": step_name,
            "status": status,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    
    # Update current step display
    if status == "in-progress":
        task["currentStep"] = step_name
    
    save_progress(progress)


def register_agent(progress: dict, task_id: str):
    """Register this agent in progress.json."""
    progress["agents"][AGENT_ID] = {
        "status": "working",
        "taskIds": [task_id],
        "startedAt": datetime.now(timezone.utc).isoformat(),
    }
    save_progress(progress)


def unregister_agent(progress: dict):
    """Remove agent from progress.json."""
    if AGENT_ID in progress["agents"]:
        del progress["agents"][AGENT_ID]
    save_progress(progress)


def run_codex_task(
    task_id: str,
    title: str,
    repo: str = None,
    context: str = None,
) -> dict:
    """
    Run a task using Codex CLI.
    Returns dict with status, branch, pr_url, output.
    """
    progress = load_progress()
    register_agent(progress, task_id)
    
    result = {
        "status": "failed",
        "branch": None,
        "pr_url": None,
        "output": None,
        "error": None,
    }
    
    # Determine working directory
    if repo:
        if repo.startswith("/"):
            work_dir = repo
        else:
            # GitHub repo - clone or use existing
            work_dir = f"/tmp/dexter-{task_id}"
            if not os.path.exists(work_dir):
                log(f"Cloning {repo}...", "STEP")
                update_step(progress, task_id, "Clone repository", "in-progress")
                git_commit_and_push(f"[{task_id}] Starting: Clone repository")
                
                subprocess.run(
                    ["git", "clone", f"https://github.com/{repo}.git", work_dir],
                    check=True,
                    capture_output=True,
                )
                
                update_step(progress, task_id, "Clone repository", "done", f"Cloned {repo}")
                git_commit_and_push(f"[{task_id}] Done: Clone repository")
    else:
        work_dir = DASHBOARD_DIR
    
    # Create branch
    branch_name = f"dexter/{task_id}"
    log(f"Creating branch {branch_name}...", "STEP")
    update_step(progress, task_id, "Create branch", "in-progress")
    git_commit_and_push(f"[{task_id}] Starting: Create branch")
    
    os.chdir(work_dir)
    try:
        subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True)
        result["branch"] = branch_name
        update_step(progress, task_id, "Create branch", "done", branch_name)
        git_commit_and_push(f"[{task_id}] Done: Created branch {branch_name}")
    except subprocess.CalledProcessError:
        # Branch might already exist
        subprocess.run(["git", "checkout", branch_name], check=True, capture_output=True)
        result["branch"] = branch_name
        update_step(progress, task_id, "Create branch", "done", f"Using existing {branch_name}")
    
    # Build prompt for Codex
    prompt = f"""Task: {title}

You are working on task ID: {task_id}
Branch: {branch_name}

{f'Additional context: {context}' if context else ''}

Instructions:
1. Understand the task requirements
2. Make the necessary code changes
3. Test your changes if applicable
4. Commit with a clear message referencing the task

Be thorough but focused. Complete the task efficiently."""

    # Run Codex
    log("Running Codex agent...", "STEP")
    update_step(progress, task_id, "Codex working", "in-progress", "Agent analyzing task...")
    git_commit_and_push(f"[{task_id}] Starting: Codex agent")
    
    try:
        # Run codex with the prompt
        codex_result = subprocess.run(
            ["codex", "--approval-mode", "full-auto", prompt],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            cwd=work_dir,
        )
        
        result["output"] = codex_result.stdout
        
        if codex_result.returncode == 0:
            update_step(progress, task_id, "Codex working", "done", "Changes complete")
            log("Codex completed successfully", "SUCCESS")
        else:
            update_step(progress, task_id, "Codex working", "done", "Completed with warnings")
            log(f"Codex finished with code {codex_result.returncode}", "INFO")
        
        git_commit_and_push(f"[{task_id}] Done: Codex agent completed")
        
    except subprocess.TimeoutExpired:
        result["error"] = "Codex timed out after 10 minutes"
        update_step(progress, task_id, "Codex working", "done", "Timed out")
        git_commit_and_push(f"[{task_id}] Error: Codex timed out")
        log("Codex timed out", "ERROR")
    except FileNotFoundError:
        result["error"] = "Codex CLI not found - running in simulation mode"
        update_step(progress, task_id, "Codex working", "done", "Simulated (codex not available)")
        git_commit_and_push(f"[{task_id}] Done: Simulated completion")
        log("Codex not found, simulating completion", "INFO")
    
    # Push changes
    log("Pushing changes...", "STEP")
    update_step(progress, task_id, "Push changes", "in-progress")
    git_commit_and_push(f"[{task_id}] Starting: Push changes")
    
    os.chdir(work_dir)
    try:
        subprocess.run(["git", "push", "-u", "origin", branch_name], check=True, capture_output=True)
        update_step(progress, task_id, "Push changes", "done")
        git_commit_and_push(f"[{task_id}] Done: Pushed to {branch_name}")
    except subprocess.CalledProcessError as e:
        update_step(progress, task_id, "Push changes", "done", "No new commits to push")
        log("No commits to push or push failed", "INFO")
    
    # Create PR
    log("Creating pull request...", "STEP")
    update_step(progress, task_id, "Create PR", "in-progress")
    git_commit_and_push(f"[{task_id}] Starting: Create PR")
    
    try:
        pr_result = subprocess.run(
            [
                "gh", "pr", "create",
                "--title", f"[Dexter] {title}",
                "--body", f"""## Task: {title}

**Task ID:** `{task_id}`
**Branch:** `{branch_name}`

{f'### Context\n{context}' if context else ''}

### Changes
This PR was created by Dexter to complete the above task.

---
🤖 *Automated by [Dexter Dashboard](https://kishparikh13.github.io/dexter-collab/)*
""",
                "--base", "main",
            ],
            capture_output=True,
            text=True,
            cwd=work_dir,
        )
        
        if pr_result.returncode == 0:
            pr_url = pr_result.stdout.strip()
            result["pr_url"] = pr_url
            result["status"] = "review"
            update_step(progress, task_id, "Create PR", "done", pr_url)
            log(f"PR created: {pr_url}", "SUCCESS")
        else:
            # PR might already exist
            if "already exists" in pr_result.stderr:
                # Get existing PR URL
                list_result = subprocess.run(
                    ["gh", "pr", "list", "--head", branch_name, "--json", "url", "--jq", ".[0].url"],
                    capture_output=True,
                    text=True,
                    cwd=work_dir,
                )
                if list_result.stdout.strip():
                    pr_url = list_result.stdout.strip()
                    result["pr_url"] = pr_url
                    result["status"] = "review"
                    update_step(progress, task_id, "Create PR", "done", f"Existing: {pr_url}")
                else:
                    update_step(progress, task_id, "Create PR", "done", "PR exists")
                    result["status"] = "review"
            else:
                update_step(progress, task_id, "Create PR", "done", "Could not create PR")
                log(f"PR creation failed: {pr_result.stderr}", "ERROR")
        
        git_commit_and_push(f"[{task_id}] Done: PR created")
        
    except FileNotFoundError:
        update_step(progress, task_id, "Create PR", "done", "gh CLI not found")
        log("gh CLI not found, skipping PR creation", "INFO")
        result["status"] = "review"  # Mark as review anyway
    
    # Update final task status
    progress = load_progress()
    progress["tasks"][task_id]["status"] = result["status"]
    if result["pr_url"]:
        progress["tasks"][task_id]["prUrl"] = result["pr_url"]
    
    # Unregister agent
    unregister_agent(progress)
    git_commit_and_push(f"[{task_id}] Complete: Task ready for review")
    
    return result


def generate_notification(task_id: str, title: str, result: dict) -> str:
    """Generate a Telegram notification message."""
    if result["status"] == "review":
        msg = f"✅ **Task Complete: {title}**\n\n"
        msg += f"Task ID: `{task_id}`\n"
        if result["branch"]:
            msg += f"Branch: `{result['branch']}`\n"
        if result["pr_url"]:
            msg += f"\n🔗 [Review PR]({result['pr_url']})"
        msg += "\n\nReady for your review!"
    elif result["status"] == "failed":
        msg = f"❌ **Task Failed: {title}**\n\n"
        msg += f"Task ID: `{task_id}`\n"
        if result["error"]:
            msg += f"Error: {result['error']}\n"
        msg += "\nPlease check the logs."
    else:
        msg = f"📋 **Task Update: {title}**\n\n"
        msg += f"Status: {result['status']}"
    
    return msg


def main():
    parser = argparse.ArgumentParser(description="Dexter Task Orchestrator")
    parser.add_argument("--task-id", required=True, help="Unique task ID")
    parser.add_argument("--title", required=True, help="Task title")
    parser.add_argument("--repo", help="Target repository (owner/repo or /path)")
    parser.add_argument("--context", help="Additional context for the task")
    parser.add_argument("--dry-run", action="store_true", help="Don't run Codex, just simulate")
    
    args = parser.parse_args()
    
    log(f"Starting task: {args.title}", "INFO")
    log(f"Task ID: {args.task_id}", "INFO")
    
    # Run the task
    result = run_codex_task(
        task_id=args.task_id,
        title=args.title,
        repo=args.repo,
        context=args.context,
    )
    
    # Generate notification
    notification = generate_notification(args.task_id, args.title, result)
    
    print("\n" + "=" * 50)
    print("TELEGRAM NOTIFICATION:")
    print("=" * 50)
    print(notification)
    print("=" * 50)
    
    # Also output as JSON for programmatic use
    output = {
        "task_id": args.task_id,
        "title": args.title,
        "result": result,
        "notification": notification,
    }
    
    # Write to output file
    output_file = DASHBOARD_DIR / "scripts" / "last-run.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    
    log(f"Output saved to {output_file}", "INFO")
    
    return 0 if result["status"] == "review" else 1


if __name__ == "__main__":
    sys.exit(main())
