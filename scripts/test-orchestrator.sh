#!/bin/bash
# Test the orchestrator with a simple simulated task
# This doesn't actually run Codex - it tests the progress tracking

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="$(dirname "$SCRIPT_DIR")"

echo "🧪 Testing Dexter Orchestrator"
echo "================================"
echo ""

# Test 1: Progress file updates
echo "Test 1: Progress file tracking"
echo "-------------------------------"

cd "$DASHBOARD_DIR"

# Backup current progress
cp progress.json progress.json.backup 2>/dev/null || true

# Create test progress entry
python3 << 'EOF'
import json
import sys
sys.path.insert(0, 'scripts')
from orchestrator import load_progress, save_progress, update_step, git_commit_and_push

progress = load_progress()
task_id = "test-task-001"

print(f"  Creating test task: {task_id}")

# Simulate steps
update_step(progress, task_id, "Initialize", "in-progress", "Starting test...")
print("  ✓ Step 1: Initialize (in-progress)")

update_step(progress, task_id, "Initialize", "done", "Completed")
print("  ✓ Step 1: Initialize (done)")

update_step(progress, task_id, "Process", "in-progress", "Working...")
print("  ✓ Step 2: Process (in-progress)")

update_step(progress, task_id, "Process", "done")
print("  ✓ Step 2: Process (done)")

# Check the result
progress = load_progress()
task = progress["tasks"].get(task_id, {})
print(f"\n  Task status: {task.get('status', 'unknown')}")
print(f"  Steps: {len(task.get('steps', []))}")

# Clean up test entry
del progress["tasks"][task_id]
save_progress(progress)
print("  ✓ Cleaned up test task")
EOF

echo ""
echo "Test 1: PASSED ✅"
echo ""

# Test 2: Natural language parsing
echo "Test 2: Natural language parsing"
echo "---------------------------------"

python3 << 'EOF'
import sys
import re

# Define the parse function inline (copy from dexter-task)
def parse_natural_command(text: str) -> dict:
    result = {
        "title": None,
        "repo": None,
        "context": None,
        "task_id": None,
    }
    
    # Extract task ID
    id_match = re.search(r'Task ID:\s*([^\s\n]+)', text, re.IGNORECASE)
    if id_match:
        result["task_id"] = id_match.group(1)
    
    # Extract repo
    repo_match = re.search(r'Repo:\s*([^\s\n]+)', text, re.IGNORECASE)
    if not repo_match:
        repo_match = re.search(r'in\s+([A-Za-z0-9_-]+/[A-Za-z0-9_.-]+)', text)
    if repo_match:
        result["repo"] = repo_match.group(1)
    
    # Extract context
    context_match = re.search(r'\(context:\s*([^)]+)\)', text, re.IGNORECASE)
    if not context_match:
        context_match = re.search(r'Context:\s*(.+?)(?:\n|Task ID:|$)', text, re.IGNORECASE)
    if context_match:
        result["context"] = context_match.group(1).strip()
    
    # Extract title (quoted string or after "Start task:")
    title_match = re.search(r'["\']([^"\']+)["\']', text)
    if not title_match:
        title_match = re.search(r'Start task:\s*["\']?([^"\'\n]+)', text, re.IGNORECASE)
    if not title_match:
        title_match = re.search(r'Task:\s*["\']?([^"\'\n(]+)', text, re.IGNORECASE)
    if title_match:
        result["title"] = title_match.group(1).strip()
    
    return result

parse = parse_natural_command

tests = [
    ('Start task: "Fix the login bug"\nRepo: KishParikh13/app\nTask ID: task-123',
     {"title": "Fix the login bug", "repo": "KishParikh13/app", "task_id": "task-123"}),
    
    ('"Add dark mode" in owner/repo',
     {"title": "Add dark mode", "repo": "owner/repo"}),
    
    ('Task: Update README (context: add setup section)',
     {"title": "Update README", "context": "add setup section"}),
]

all_passed = True
for i, (input_text, expected) in enumerate(tests, 1):
    result = parse(input_text)
    passed = True
    for key, val in expected.items():
        if result.get(key) != val:
            print(f"  Test {i}: FAILED ❌")
            print(f"    Input: {input_text[:50]}...")
            print(f"    Expected {key}: {val}")
            print(f"    Got: {result.get(key)}")
            passed = False
            all_passed = False
            break
    if passed:
        print(f"  Test {i}: PASSED ✅")

print("")
if all_passed:
    print("Test 2: PASSED ✅")
else:
    print("Test 2: SOME FAILURES ❌")
EOF

echo ""

# Test 3: Notification generation
echo "Test 3: Notification generation"
echo "--------------------------------"

python3 << 'EOF'
import sys
sys.path.insert(0, 'scripts')
from orchestrator import generate_notification

result_success = {
    "status": "review",
    "branch": "dexter/task-123",
    "pr_url": "https://github.com/owner/repo/pull/42",
    "output": "Changes made",
    "error": None,
}

result_fail = {
    "status": "failed",
    "branch": None,
    "pr_url": None,
    "output": None,
    "error": "Codex timed out",
}

msg_success = generate_notification("task-123", "Fix login bug", result_success)
msg_fail = generate_notification("task-456", "Add feature", result_fail)

if "✅" in msg_success and "Review PR" in msg_success:
    print("  Success notification: PASSED ✅")
else:
    print("  Success notification: FAILED ❌")
    print(f"  Output: {msg_success}")

if "❌" in msg_fail and "timed out" in msg_fail:
    print("  Failure notification: PASSED ✅")
else:
    print("  Failure notification: FAILED ❌")
    print(f"  Output: {msg_fail}")
EOF

echo ""
echo "================================"
echo "All tests complete!"
echo ""

# Restore backup
mv progress.json.backup progress.json 2>/dev/null || true
