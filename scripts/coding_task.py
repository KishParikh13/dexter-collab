#!/usr/bin/env python3
"""
Coding Task Module for Dexter

This module provides functions for Dexter to manage coding tasks:
- Create task entries in progress.json
- Commit and push progress updates
- Designed to work with Moltbot subagents

Usage from Dexter (main agent):
    
    # 1. Import and create a task
    from scripts.coding_task import create_task, update_progress, complete_task
    
    task = create_task(
        title="Add favicon to dexter-collab",
        repo="/data/workspace/dexter-collab",  # or "owner/repo" for GitHub
        context="Add a simple emoji favicon using SVG"
    )
    
    # 2. Spawn a subagent with the task prompt
    # (Dexter does this via exec with moltbot spawn-agent or similar)
    
    # 3. The subagent uses update_progress() as it works
    # 4. Subagent calls complete_task() when done
"""

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Configuration
DASHBOARD_DIR = Path("/data/workspace/dexter-collab")
PROGRESS_FILE = DASHBOARD_DIR / "progress.json"


def _now_iso() -> str:
    """Current time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _generate_task_id() -> str:
    """Generate a unique task ID."""
    return f"task-{int(time.time())}-{os.urandom(3).hex()}"


def load_progress() -> dict:
    """Load progress.json."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"tasks": {}, "agents": {}, "lastUpdated": None}


def save_progress(progress: dict):
    """Save progress.json."""
    progress["lastUpdated"] = _now_iso()
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def git_sync(message: str) -> bool:
    """
    Commit and push progress.json changes.
    
    If on main branch: commit and push directly.
    If on feature branch: commit locally (progress will sync on merge).
    
    For real-time dashboard updates, call sync_progress_to_main() explicitly.
    """
    try:
        os.chdir(DASHBOARD_DIR)
        
        subprocess.run(["git", "add", "progress.json"], check=True, capture_output=True)
        
        # Check if there are changes
        result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
        if result.returncode == 0:
            return True  # No changes
        
        subprocess.run(["git", "commit", "-m", message], check=True, capture_output=True)
        
        # Only push if on main
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        )
        if result.stdout.strip() == "main":
            subprocess.run(["git", "push"], check=True, capture_output=True)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git sync error: {e}")
        return False


def sync_progress_to_main() -> bool:
    """
    Force sync progress.json to main branch for dashboard visibility.
    
    Call this after completing a task or at key checkpoints.
    """
    try:
        os.chdir(DASHBOARD_DIR)
        
        # Get current branch
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        )
        current_branch = result.stdout.strip()
        
        if current_branch == "main":
            # Already on main, just push
            subprocess.run(["git", "push"], check=True, capture_output=True)
            return True
        
        # Save current progress.json content
        with open(PROGRESS_FILE) as f:
            progress_content = f.read()
        
        # Switch to main briefly
        subprocess.run(["git", "stash", "push", "-m", "temp"], capture_output=True)
        subprocess.run(["git", "checkout", "main"], check=True, capture_output=True)
        subprocess.run(["git", "pull", "--rebase"], capture_output=True)
        
        # Write and commit progress
        with open(PROGRESS_FILE, "w") as f:
            f.write(progress_content)
        
        subprocess.run(["git", "add", "progress.json"], check=True, capture_output=True)
        result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
        if result.returncode != 0:
            subprocess.run(["git", "commit", "-m", "Update task progress"], check=True, capture_output=True)
            subprocess.run(["git", "push"], check=True, capture_output=True)
        
        # Return to feature branch
        subprocess.run(["git", "checkout", current_branch], check=True, capture_output=True)
        subprocess.run(["git", "stash", "pop"], capture_output=True)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Sync to main error: {e}")
        return False


def create_task(
    title: str,
    repo: str,
    context: str = "",
    task_id: str = None,
) -> dict:
    """
    Create a new coding task and add it to progress.json.
    
    Args:
        title: Task title/description
        repo: Path to repo (/data/workspace/...) or GitHub repo (owner/repo)
        context: Additional context for the coding agent
        task_id: Optional custom task ID (auto-generated if not provided)
    
    Returns:
        Task dict with id, title, repo, context, branch, status
    """
    task_id = task_id or _generate_task_id()
    branch = f"dexter/{task_id}"
    
    task = {
        "id": task_id,
        "title": title,
        "repo": repo,
        "context": context,
        "branch": branch,
        "status": "in-progress",
        "currentStep": "Initializing",
        "steps": [
            {"name": "Task created", "status": "done", "timestamp": _now_iso()}
        ],
        "createdAt": _now_iso(),
        "prUrl": None,
    }
    
    # Add to progress.json
    progress = load_progress()
    progress["tasks"][task_id] = task
    save_progress(progress)
    git_sync(f"[{task_id}] Task created: {title}")
    
    return task


def update_progress(
    task_id: str,
    step_name: str,
    status: str = "in-progress",
    detail: str = None,
):
    """
    Update progress for a task step.
    
    Args:
        task_id: The task ID
        step_name: Name of the current step
        status: "pending", "in-progress", or "done"
        detail: Optional detail text
    """
    progress = load_progress()
    task = progress["tasks"].get(task_id)
    if not task:
        print(f"Task {task_id} not found")
        return
    
    # Find or create step
    step = next((s for s in task["steps"] if s["name"] == step_name), None)
    if step:
        step["status"] = status
        if detail:
            step["detail"] = detail
        step["timestamp"] = _now_iso()
    else:
        task["steps"].append({
            "name": step_name,
            "status": status,
            "detail": detail,
            "timestamp": _now_iso(),
        })
    
    # Update current step display
    if status == "in-progress":
        task["currentStep"] = step_name
    
    save_progress(progress)
    git_sync(f"[{task_id}] {step_name}: {status}")


def complete_task(
    task_id: str,
    pr_url: str = None,
    summary: str = None,
) -> str:
    """
    Mark a task as complete and ready for review.
    
    Args:
        task_id: The task ID
        pr_url: URL to the pull request
        summary: Brief summary of what was done
    
    Returns:
        Notification message for Telegram
    """
    progress = load_progress()
    task = progress["tasks"].get(task_id)
    if not task:
        return f"❌ Task {task_id} not found"
    
    task["status"] = "review"
    task["currentStep"] = "Ready for review"
    task["completedAt"] = _now_iso()
    if pr_url:
        task["prUrl"] = pr_url
    if summary:
        task["summary"] = summary
    
    # Add completion step
    task["steps"].append({
        "name": "Complete",
        "status": "done",
        "detail": summary or "Task completed",
        "timestamp": _now_iso(),
    })
    
    save_progress(progress)
    git_sync(f"[{task_id}] Complete: Ready for review")
    
    # Generate notification
    msg = f"✅ **Task Complete: {task['title']}**\n\n"
    if summary:
        msg += f"{summary}\n\n"
    if pr_url:
        msg += f"🔗 [Review PR]({pr_url})\n"
    msg += f"\nTask ID: `{task_id}`"
    
    return msg


def fail_task(task_id: str, error: str) -> str:
    """Mark a task as failed."""
    progress = load_progress()
    task = progress["tasks"].get(task_id)
    if not task:
        return f"Task {task_id} not found"
    
    task["status"] = "failed"
    task["currentStep"] = "Failed"
    task["error"] = error
    task["steps"].append({
        "name": "Failed",
        "status": "done",
        "detail": error,
        "timestamp": _now_iso(),
    })
    
    save_progress(progress)
    git_sync(f"[{task_id}] Failed: {error[:50]}")
    
    return f"❌ **Task Failed: {task['title']}**\n\nError: {error}\n\nTask ID: `{task_id}`"


def get_task(task_id: str) -> Optional[dict]:
    """Get a task by ID."""
    progress = load_progress()
    return progress["tasks"].get(task_id)


def get_coding_agent_prompt(task: dict) -> str:
    """
    Generate the prompt for a coding subagent.
    
    This prompt instructs the subagent on how to:
    - Work on a feature branch
    - Update progress as it works
    - Create a PR when done
    - Notify completion
    """
    return f'''You are a coding agent working on a specific task. Follow these steps precisely:

## Task Details
- **Title:** {task["title"]}
- **Task ID:** {task["id"]}
- **Repo:** {task["repo"]}
- **Branch:** {task["branch"]}
- **Context:** {task.get("context", "None provided")}

## Instructions

### 1. Setup (update progress after each)
```python
import sys
sys.path.insert(0, "/data/workspace/dexter-collab/scripts")
from coding_task import update_progress, complete_task, fail_task

TASK_ID = "{task["id"]}"
```

### 2. Create feature branch
```bash
cd {task["repo"]}
git checkout -b {task["branch"]}
```
Then: `update_progress(TASK_ID, "Create branch", "done")`

### 3. Make changes
- Understand the requirements
- Make the necessary code changes
- Test if applicable

Update progress as you work:
```python
update_progress(TASK_ID, "Making changes", "in-progress", "Working on X...")
# ... do work ...
update_progress(TASK_ID, "Making changes", "done", "Completed X")
```

### 4. Commit and push
```bash
git add -A
git commit -m "[{task["id"]}] {task["title"]}"
git push -u origin {task["branch"]}
```
Then: `update_progress(TASK_ID, "Push changes", "done")`

### 5. Create PR
```bash
gh pr create --title "[Dexter] {task["title"]}" --body "Task ID: {task["id"]}" --base main
```
Capture the PR URL from the output.

### 6. Complete and notify
```python
notification = complete_task(TASK_ID, pr_url="<PR_URL>", summary="<brief summary>")
print(notification)
```

Then wake the main agent:
```bash
moltbot gateway call agent.wake --params '{{"text": "<notification>", "channel": "telegram"}}'
```

### Error Handling
If something fails:
```python
fail_task(TASK_ID, "Description of what went wrong")
```

## Important
- Update progress.json after EACH major step (it auto-commits to GitHub)
- The dashboard polls progress.json every 15 seconds
- Keep commits clean and focused
- Don't modify files outside the task scope
'''


# CLI interface for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Coding Task Manager")
    subparsers = parser.add_subparsers(dest="command")
    
    # Create
    create_p = subparsers.add_parser("create", help="Create a new task")
    create_p.add_argument("title", help="Task title")
    create_p.add_argument("--repo", required=True, help="Repo path")
    create_p.add_argument("--context", default="", help="Additional context")
    
    # Update
    update_p = subparsers.add_parser("update", help="Update task progress")
    update_p.add_argument("task_id", help="Task ID")
    update_p.add_argument("step", help="Step name")
    update_p.add_argument("--status", default="in-progress", help="Step status")
    update_p.add_argument("--detail", help="Step detail")
    
    # Complete
    complete_p = subparsers.add_parser("complete", help="Complete a task")
    complete_p.add_argument("task_id", help="Task ID")
    complete_p.add_argument("--pr-url", help="PR URL")
    complete_p.add_argument("--summary", help="Summary")
    
    # Prompt
    prompt_p = subparsers.add_parser("prompt", help="Generate agent prompt")
    prompt_p.add_argument("task_id", help="Task ID")
    
    args = parser.parse_args()
    
    if args.command == "create":
        task = create_task(args.title, args.repo, args.context)
        print(f"Created task: {task['id']}")
        print(f"Branch: {task['branch']}")
    
    elif args.command == "update":
        update_progress(args.task_id, args.step, args.status, args.detail)
        print(f"Updated {args.task_id}: {args.step} -> {args.status}")
    
    elif args.command == "complete":
        msg = complete_task(args.task_id, args.pr_url, args.summary)
        print(msg)
    
    elif args.command == "prompt":
        task = get_task(args.task_id)
        if task:
            print(get_coding_agent_prompt(task))
        else:
            print(f"Task {args.task_id} not found")
