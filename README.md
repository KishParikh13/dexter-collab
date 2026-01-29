# Dexter Dashboard 🥸

A Klaus-style task collaboration dashboard for working with your AI assistant.

**Live Demo:** https://kishparikh13.github.io/dexter-collab/

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

Just open https://kishparikh13.github.io/dexter-collab/

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
