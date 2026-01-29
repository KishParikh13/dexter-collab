# Coding Tasks Pattern for Dexter

When Kish mentions a coding task that references a specific repo or folder, use this pattern to hand it off to a coding subagent while keeping the main chat free.

## Detection Heuristics

A message is likely a coding task if it:
- Mentions a specific repo (e.g., "in dexter-collab", "KishParikh13/repo")
- References a file path or folder
- Asks for code changes (add, fix, update, refactor, implement)
- Is a clear engineering task vs. a quick question

**Examples that should trigger this pattern:**
- "Add a favicon to dexter-collab"
- "Fix the login bug in the auth repo"  
- "Update the README in /data/workspace/project"
- "Implement dark mode for the dashboard"

**Examples that should NOT trigger (handle directly):**
- "What's in progress.json?"
- "Show me the folder structure"
- "Explain how X works"
- Quick file edits that take <2 minutes

## The Pattern

### Step 1: Create the task

```python
import sys
sys.path.insert(0, "/data/workspace/dexter-collab/scripts")
from coding_task import create_task, get_coding_agent_prompt

# Create task entry in progress.json (auto-commits to GitHub)
task = create_task(
    title="Add favicon to dexter-collab",
    repo="/data/workspace/dexter-collab",
    context="Use an SVG emoji favicon for simplicity"
)

print(f"Created task {task['id']} on branch {task['branch']}")
```

### Step 2: Spawn a coding subagent

```bash
# Get the prompt for the coding agent
python3 -c "
import sys
sys.path.insert(0, '/data/workspace/dexter-collab/scripts')
from coding_task import get_task, get_coding_agent_prompt
task = get_task('TASK_ID_HERE')
print(get_coding_agent_prompt(task))
" > /tmp/coding-prompt.txt

# Spawn subagent with the prompt
# Option A: Use Moltbot's subagent spawning
exec moltbot agent spawn --prompt "$(cat /tmp/coding-prompt.txt)" --background

# Option B: Use Codex directly  
exec codex --approval-mode full-auto "$(cat /tmp/coding-prompt.txt)"
```

### Step 3: Respond to Kish

After spawning, immediately respond:

```
🚀 **On it!** I've started working on that.

**Task:** Add favicon to dexter-collab  
**Branch:** `dexter/task-1234567890-abc123`

You can track progress on the [dashboard](https://kishparikh13.github.io/dexter-collab/).
I'll ping you when it's ready for review!
```

## What the Coding Agent Does

The spawned agent follows a strict workflow:

1. **Setup** - Import the coding_task module
2. **Branch** - Create feature branch `dexter/{task-id}`
3. **Code** - Make changes, updating progress after each step
4. **Commit** - Commit with task ID in message
5. **Push** - Push to origin
6. **PR** - Create pull request via `gh pr create`
7. **Notify** - Call `complete_task()` and wake main agent

Progress updates appear in the dashboard in real-time (15s polling).

## Completion Notification

When the coding agent finishes, it wakes the main agent with a message like:

```
✅ **Task Complete: Add favicon to dexter-collab**

Added SVG emoji favicon (🥸) to index.html

🔗 [Review PR](https://github.com/KishParikh13/dexter-collab/pull/42)

Task ID: `task-1234567890-abc123`
```

## Quick Reference

```python
# Import
from coding_task import create_task, update_progress, complete_task, fail_task, get_task, get_coding_agent_prompt

# Create task (returns task dict)
task = create_task(title, repo, context="")

# Update progress (call frequently)
update_progress(task_id, "Step name", "in-progress", "Detail...")
update_progress(task_id, "Step name", "done")

# Complete (returns notification message)
msg = complete_task(task_id, pr_url="...", summary="...")

# Fail (returns notification message)
msg = fail_task(task_id, "Error description")

# Get existing task
task = get_task(task_id)

# Get prompt for coding agent
prompt = get_coding_agent_prompt(task)
```

## Files

- `/data/workspace/dexter-collab/scripts/coding_task.py` - Main module
- `/data/workspace/dexter-collab/progress.json` - Progress data (auto-synced to GitHub)
- Dashboard: https://kishparikh13.github.io/dexter-collab/
