# Dexter Collab 🥸

A lightweight task collaboration dashboard built for working together with your AI assistant.

## Features

- **📋 Multi-Task Input** - Add multiple tasks at once (one per line)
- **📊 Status Tracking** - Pending → In Progress → Done
- **🔀 Drag & Drop** - Reorder tasks by priority
- **📝 Rich Output** - Attach markdown or JSON UI to each task
- **🎨 JSON-to-UI Rendering** - Dynamic components (tables, stats, lists, progress bars)
- **🌙 Dark Mode** - Easy on the eyes
- **💾 Local Storage** - Everything persists automatically

## Quick Start

### Option 1: Open Directly
Just open `index.html` in your browser. That's it!

### Option 2: Python Server
```bash
cd dexter-collab
python3 -m http.server 8080
# Open http://localhost:8080
```

### Option 3: Node Server
```bash
npx serve .
```

## JSON UI Components

You can render dynamic UI by putting JSON in a task's output (switch to "JSON UI" mode).

### Table
```json
{
  "type": "table",
  "columns": ["Name", "Status", "Progress"],
  "rows": [
    ["Task A", "Done", "100%"],
    ["Task B", "In Progress", "60%"]
  ]
}
```

### Stats Grid
```json
{
  "type": "stats",
  "items": [
    {"label": "Tasks", "value": 12},
    {"label": "Done", "value": 8},
    {"label": "Hours", "value": 4.5}
  ]
}
```

### Progress Bar
```json
{
  "type": "progress",
  "label": "Sprint Progress",
  "value": 75,
  "color": "bg-green-500"
}
```

### List
```json
{
  "type": "list",
  "items": [
    {"icon": "✅", "text": "Completed item"},
    {"icon": "⏳", "text": "Pending item"}
  ]
}
```

### Card
```json
{
  "type": "card",
  "title": "Summary",
  "description": "Here's what we accomplished today.",
  "footer": "Updated 5 minutes ago"
}
```

### Code Block
```json
{
  "type": "code",
  "language": "javascript",
  "code": "const hello = 'world';"
}
```

## How We Use This

1. **Kish adds tasks** - Multiple at once, priorities by order
2. **Dexter works through them** - Updates status, adds output
3. **Rich output** - Not just text dumps, but formatted results
4. **Async collaboration** - Check in anytime, see progress

## Tech Stack

- **Tailwind CSS** - Styling (via CDN)
- **Alpine.js** - Reactivity
- **marked.js** - Markdown rendering
- **Sortable.js** - Drag and drop
- **localStorage** - Persistence

No build step. No dependencies to install. Just works.

---

Built with 🥸 by Dexter
