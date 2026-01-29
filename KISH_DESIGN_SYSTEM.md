# Kish Design System

A minimalist, monospace-first design system for building clean, functional apps.

## Philosophy

- **Stark minimalism** — No decoration, pure function
- **Monospace typography** — Developer-friendly, precise
- **High contrast** — Black and white, clear hierarchy
- **No border-radius** — Sharp, intentional edges
- **No shadows** — Flat, honest design
- **Borders define space** — 1px lines create structure

---

## Colors

```css
:root {
  --bg: #000;           /* Pure black background */
  --fg: #fff;           /* Pure white foreground */
  --border: #333;       /* Subtle borders */
  --muted: #666;        /* Secondary text, labels */
  --accent: #fff;       /* Accent (same as fg) */
  --hover-bg: #111;     /* Hover background */
  --error: #f44;        /* Error/delete red */
  --success: #4f4;      /* Success green (use sparingly) */
}
```

### Usage

| Element | Color |
|---------|-------|
| Background | `var(--bg)` #000 |
| Text | `var(--fg)` #fff |
| Labels, secondary text | `var(--muted)` #666 |
| Borders | `var(--border)` #333 |
| Hover states | `var(--hover-bg)` #111 |
| Delete buttons | `var(--error)` #f44 |

---

## Typography

### Font Stack

```css
font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
```

### Scale

| Use | Size | Weight | Transform |
|-----|------|--------|-----------|
| Body text | 13px | 400 | none |
| Page title | 14px | 500 | none |
| Section title | 18px | 500 | none |
| Column header | 11px | 500 | uppercase, letter-spacing: 1px |
| Label | 10px | 500 | uppercase, letter-spacing: 0.5px |
| Meta/timestamp | 10-11px | 400 | uppercase, letter-spacing: 0.5px |
| Button | 11-12px | 400 | uppercase, letter-spacing: 0.5px |

### Key Patterns

```css
/* Labels (form fields, section headers) */
.label {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--muted);
}

/* Column/section headers */
.column-header {
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* Body text */
.body {
  font-size: 13px;
  line-height: 1.6;
}

/* Title with slight negative tracking */
.title {
  font-size: 14px;
  font-weight: 500;
  letter-spacing: -0.5px;
}
```

---

## Spacing

### Base Unit: 4px

| Token | Value | Use |
|-------|-------|-----|
| `--space-1` | 4px | Tight gaps |
| `--space-2` | 8px | Small padding, gaps |
| `--space-3` | 12px | Standard padding |
| `--space-4` | 16px | Section padding |
| `--space-6` | 24px | Large padding |

### Common Patterns

```css
/* Compact padding (buttons, tags) */
padding: 6px 12px;

/* Standard padding (cards, inputs) */
padding: 10px 12px;

/* Section padding */
padding: 12px 16px;

/* Page padding */
padding: 20px 24px;

/* Gaps between items */
gap: 8px;     /* tight */
gap: 12px;    /* standard */
gap: 16px;    /* loose */
```

---

## Components

### Buttons

```css
/* Base button */
.btn {
  background: var(--bg);
  color: var(--fg);
  border: 1px solid var(--border);
  padding: 8px 16px;
  cursor: pointer;
  font-size: 11px;
  font-family: inherit;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.btn:hover {
  border-color: var(--fg);
}

/* Primary button (inverted) */
.btn-primary {
  background: var(--fg);
  color: var(--bg);
  border-color: var(--fg);
}

.btn-primary:hover {
  background: var(--bg);
  color: var(--fg);
}

/* Danger button */
.btn-danger {
  color: var(--error);
  border-color: var(--error);
}

.btn-danger:hover {
  background: var(--error);
  color: var(--bg);
}

/* Small button */
.btn-small {
  padding: 6px 12px;
  font-size: 10px;
}
```

### Inputs

```css
input, textarea, select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--fg);
  font-size: 13px;
  font-family: inherit;
}

input:focus, textarea:focus, select:focus {
  outline: none;
  border-color: var(--fg);
}

input::placeholder, textarea::placeholder {
  color: var(--muted);
}

textarea {
  min-height: 80px;
  resize: vertical;
}
```

### Cards

```css
.card {
  background: var(--bg);
  border: 1px solid var(--border);
  padding: 12px;
  cursor: pointer;
  transition: border-color 0.1s;
}

.card:hover {
  border-color: var(--fg);
}

/* Card in grid */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
}

.card-grid .card {
  background: var(--bg);
}
```

### Modals

```css
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  background: var(--bg);
  border: 1px solid var(--border);
  padding: 24px;
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 24px;
}

.modal-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}
```

### Navigation

```css
nav {
  background: var(--bg);
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 20px;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
}

nav h1 {
  font-size: 14px;
  font-weight: 500;
  letter-spacing: -0.5px;
}

.nav-links {
  display: flex;
  gap: 4px;
}

.nav-links a {
  color: var(--muted);
  text-decoration: none;
  padding: 6px 12px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border: 1px solid transparent;
}

.nav-links a:hover {
  color: var(--fg);
}

.nav-links a.active {
  color: var(--fg);
  border-color: var(--border);
}
```

### Sidebar

```css
.sidebar {
  width: 240px;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-section {
  padding: 12px;
  border-bottom: 1px solid var(--border);
}

.sidebar-section h2 {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--muted);
  margin-bottom: 10px;
}
```

### Lists

```css
.list-item {
  padding: 8px 10px;
  cursor: pointer;
  border: 1px solid transparent;
  font-size: 12px;
}

.list-item:hover {
  border-color: var(--border);
}

.list-item.active {
  border-color: var(--fg);
}
```

### Tags

```css
.tag {
  font-size: 11px;
  color: var(--muted);
  padding: 4px 8px;
  border: 1px solid var(--border);
}
```

### Empty State

```css
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--muted);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
```

---

## Layout Patterns

### Kanban Board

```css
.board {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  min-height: calc(100vh - 90px);
}

.column {
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
}

.column:last-child {
  border-right: none;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}
```

### Two-Column (Sidebar + Content)

```css
.layout {
  display: flex;
  min-height: 100vh;
}

.sidebar { width: 240px; }
.content { flex: 1; padding: 24px; overflow-y: auto; }
```

### Grid Cards

```css
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}
```

---

## Interactions

### Hover States

```css
/* Border highlight */
.interactive:hover {
  border-color: var(--fg);
}

/* Background highlight */
.interactive:hover {
  background: var(--hover-bg);
}
```

### Drag and Drop

```css
.draggable {
  cursor: grab;
}

.draggable:active {
  cursor: grabbing;
}

.draggable.dragging {
  opacity: 0.3;
}

.drop-target.drag-over {
  background: var(--hover-bg);
}
```

### Focus States

```css
input:focus, textarea:focus, select:focus {
  outline: none;
  border-color: var(--fg);
}
```

---

## Responsive Breakpoints

```css
@media (max-width: 1000px) {
  .board { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 600px) {
  .board { grid-template-columns: 1fr; }
  .sidebar { display: none; }
}
```

---

## Scrollbars

```css
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: var(--bg);
}

::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--muted);
}
```

---

## Quick Reference

### Reset

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
```

### Base HTML

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>App Name</title>
  <style>
    :root {
      --bg: #000;
      --fg: #fff;
      --border: #333;
      --muted: #666;
    }
    
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
      font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
      background: var(--bg);
      color: var(--fg);
      font-size: 13px;
      min-height: 100vh;
    }
  </style>
</head>
<body>
  <!-- Content -->
</body>
</html>
```

---

## Don'ts

❌ Don't use border-radius (except scrollbar)
❌ Don't use box-shadow
❌ Don't use gradients
❌ Don't use colors other than the palette
❌ Don't use fonts other than monospace
❌ Don't use bold (use medium/500 max)
❌ Don't center large blocks of text
❌ Don't use icons (use emoji sparingly)

## Do's

✅ Use 1px borders for structure
✅ Use uppercase + letter-spacing for labels
✅ Use hover border-color for interactivity
✅ Use high contrast (black/white)
✅ Keep spacing tight and intentional
✅ Use the grid for layouts
✅ Keep it simple and functional

---

*Last updated: January 2026*
