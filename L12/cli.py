import json
import os
import sys
import argparse
from datetime import datetime

TASKS_FILE = "tasks.json"
ARCHIVE_FILE = "archive.json"

def load_json(filename):
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving to {filename}: {e}", file=sys.stderr)

def cmd_add(description, priority):
    tasks = load_json(TASKS_FILE)
    new_id = max([t.get("id", 0) for t in tasks] + [0]) + 1
    new_task = {
        "id": new_id,
        "description": description,
        "status": "pending",
        "priority": priority,
        "created_at": datetime.now().isoformat()
    }
    tasks.append(new_task)
    save_json(TASKS_FILE, tasks)
    print(f"Added task {new_id} with priority '{priority}'.")

def cmd_list():
    tasks = load_json(TASKS_FILE)
    if not tasks:
        print("No tasks found.")
        return

    # Priority mapping for sorting (higher number = higher priority)
    priority_order = {"high": 3, "medium": 2, "low": 1}

    # Sort tasks: high first, then medium, then low. Unspecified priority defaults to medium.
    def get_sort_key(task):
        p = task.get("priority", "medium").lower()
        return -priority_order.get(p, 2)  # negative for descending order

    sorted_tasks = sorted(tasks, key=get_sort_key)

    print("\n=== Tasks (Sorted by Priority) ===")
    for t in sorted_tasks:
        status_symbol = "[X]" if t.get("status") == "complete" else "[ ]"
        p = t.get("priority", "medium").upper()
        print(f"{t.get('id')}. {status_symbol} {t.get('description')} [Priority: {p}]")
    print("===================================\n")

def cmd_complete(task_id):
    tasks = load_json(TASKS_FILE)
    found = False
    for t in tasks:
        if t.get("id") == task_id:
            t["status"] = "complete"
            found = True
            break
    if found:
        save_json(TASKS_FILE, tasks)
        print(f"Completed task {task_id}.")
    else:
        print(f"Error: Task with ID {task_id} not found.", file=sys.stderr)
        sys.exit(1)

def cmd_delete(task_id):
    tasks = load_json(TASKS_FILE)
    archive = load_json(ARCHIVE_FILE)
    
    target_task = None
    for t in tasks:
        if t.get("id") == task_id:
            target_task = t
            break
            
    if target_task:
        # Remove from tasks
        tasks = [t for t in tasks if t.get("id") != task_id]
        save_json(TASKS_FILE, tasks)
        
        # Add to archive with deleted_at timestamp
        target_task["deleted_at"] = datetime.now().isoformat()
        archive.append(target_task)
        save_json(ARCHIVE_FILE, archive)
        
        print(f"Archived task {task_id}.")
    else:
        print(f"Error: Task with ID {task_id} not found.", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="CLI Task Manager with priority & archiving.")
    subparsers = parser.add_subparsers(dest="command")

    # Add command
    p_add = subparsers.add_parser("add", help="Add a new task")
    p_add.add_argument("description", help="Task description")
    p_add.add_argument("--priority", choices=["low", "medium", "high"], default="medium",
                       help="Task priority (default: medium)")

    # List command
    subparsers.add_parser("list", help="List all tasks sorted by priority")

    # Complete command
    p_comp = subparsers.add_parser("complete", help="Mark a task as complete")
    p_comp.add_argument("id", type=int, help="Task ID")

    # Delete command
    p_del = subparsers.add_parser("delete", help="Delete (archive) a task")
    p_del.add_argument("id", type=int, help="Task ID")

    args = parser.parse_args()

    if args.command == "add":
        cmd_add(args.description, args.priority)
    elif args.command == "list":
        cmd_list()
    elif args.command == "complete":
        cmd_complete(args.id)
    elif args.command == "delete":
        cmd_delete(args.id)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
