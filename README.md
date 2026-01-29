# Dexter Dashboard 🥸

A Klaus-style task collaboration dashboard for working with your AI assistant.

**Live Demo:** https://kish-clawdbot-controls.vercel.app

## Agent Orchestration

This dashboard integrates with Codex agents to automate task execution. When you start a task from the dashboard, Dexter:

1. Creates a working branch
2. Spawns a Codex agent to work on the task
3. Updates `progress.json` with live progress (visible in dashboard)
4. Commits and pushes changes
5. Creates a PR for review
6. Sends a Telegram notification when complete

### Quick Start

```bash
# From Telegram, send a task command:
Start task: "Fix the login bug"
Repo: KishParikh13/my-app
Task ID: task-123

# Or use the CLI directly:
./scripts/run-task.sh "Add dark mode" --repo KishParikh13/my-app --context "Use CSS variables"
```

### CLI Usage

**run-task.sh** - Main entry point:
```bash
./scripts/run-task.sh "Task Title" [options]

Options:
  --repo owner/repo    Target GitHub repository
  --context "..."      Additional context for the agent
  --task-id ID         Custom task ID (auto-generated if omitted)
```

**dexter-task** - Moltbot integration (parses natural language):
```bash
# Natural language format (from Telegram):
./scripts/dexter-task 'Start task: "Fix bug" Repo: owner/repo'

# CLI format:
./scripts/dexter-task "Add feature" --repo owner/repo --context "details"
```

### Progress Tracking

The dashboard polls `progress.json` every 15 seconds. Structure:

```json
{
  "tasks": {
    "task-123": {
      "status": "in-progress",
      "currentStep": "Codex working",
      "steps": [
        {"name": "Clone repository", "status": "done"},
        {"name": "Create branch", "status": "done"},
        {"name": "Codex working", "status": "in-progress", "detail": "Analyzing..."}
      ],
      "prUrl": null
    }
  },
  "agents": {
    "codex-1234567890": {
      "status": "working",
      "taskIds": ["task-123"]
    }
  }
}
```

### Testing

```bash
./scripts/test-orchestrator.sh
```

---

## Features

### 🎭 Agent Status
- Avatar with status indicator
- Live status: Online, Working, Waiting, Idle
- Status message shows current activity

### 📋 Kanban Board
- **To Do** - Tasks waiting to be started
- **In Progress** - Active work with live status updates
- **Done** - Completed tasks
- **Archived** - Old tasks for reference
- Drag-and-drop between columns

### 📁 Deliverables
- Track outputs, folders, files, links
- Custom icons and types
- Quick access to completed work

### 📜 Action Log
- Timestamped activity feed
- See what Dexter did and when
- Auto-logged task changes

### 📝 Notes
- Quick notes for Dexter
- Checked on every heartbeat
- Mark as seen

### 🔄 Sync
- Export/Import JSON
- Share links with encoded state
- Works offline with localStorage

## Quick Start

Just open https://kish-clawdbot-controls.vercel.app

Or run locally:
```bash
python3 -m http.server 8080
# Open http://localhost:8080
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `?` | Help |
| `a` | Add task |
| `e` | Export |
| `i` | Import |
| `Esc` | Close modal |

## How We Collaborate

1. **Kish adds tasks** via To Do column or Notes
2. **Dexter works** - moves tasks to In Progress, updates live status
3. **Output captured** - results in task output, deliverables logged
4. **Action Log** - full audit trail of what happened
5. **Sync** - export/import to share state

## Tech Stack

- HTML/CSS/JS (single file, no build)
- Tailwind CSS (CDN)
- Alpine.js (reactivity)
- Sortable.js (drag-drop)
- marked.js (markdown)
- localStorage (persistence)

---

Built with 🥸 by Dexter
