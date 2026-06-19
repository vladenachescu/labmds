import json
import os

TASKS_FILE = "tasks.json"

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    try:
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_tasks(tasks):
    try:
        with open(TASKS_FILE, "w") as f:
            json.dump(tasks, f, indent=4)
    except Exception as e:
        print(f"Error saving tasks: {e}")

def add_task(description, due_date):
    tasks = load_tasks()
    new_id = max([t.get("id", 0) for t in tasks] + [0]) + 1
    new_task = {
        "id": new_id,
        "description": description,
        "due_date": due_date,
        "status": "pending"
    }
    tasks.append(new_task)
    save_tasks(tasks)
    print(f"Added task {new_id}: '{description}' due by {due_date}.")

def complete_task(task_id):
    tasks = load_tasks()
    found = False
    for t in tasks:
        if t.get("id") == task_id:
            t["status"] = "complete"
            found = True
            break
    if found:
        save_tasks(tasks)
        print(f"Completed task {task_id}.")
    else:
        print(f"Task with ID {task_id} not found.")

def delete_task(task_id):
    tasks = load_tasks()
    initial_len = len(tasks)
    tasks = [t for t in tasks if t.get("id") != task_id]
    if len(tasks) < initial_len:
        save_tasks(tasks)
        print(f"Deleted task {task_id}.")
    else:
        print(f"Task with ID {task_id} not found.")

def list_tasks():
    tasks = load_tasks()
    if not tasks:
        print("No tasks found.")
        return
    print("\n=== TODO LIST ===")
    for t in tasks:
        status_str = "[X]" if t.get("status") == "complete" else "[ ]"
        print(f"{t.get('id')}. {status_str} {t.get('description')} (Due: {t.get('due_date')})")
    print("=================\n")

def print_help():
    print("Available commands:")
    print("  add \"<description>\" <due_date> - Add a new task (e.g., add \"Pay taxes\" 25-05-2026)")
    print("  complete <id>                 - Mark a task as completed")
    print("  delete <id>                   - Delete a task")
    print("  list                          - List all tasks")
    print("  help                          - Show this help message")
    print("  exit / quit                   - Exit the application")

def main():
    print("TODO Application REPL. Type 'help' for options.")
    while True:
        try:
            line = input("todo> ").strip()
            if not line:
                continue
            if line.lower() in ("exit", "quit"):
                print("Goodbye!")
                break
            elif line.lower() == "help":
                print_help()
            elif line.lower() == "list":
                list_tasks()
            elif line.lower().startswith("add "):
                # Simple parsing of: add "Description" date
                rest = line[4:].strip()
                if rest.startswith('"'):
                    end_quote = rest.find('"', 1)
                    if end_quote != -1:
                        desc = rest[1:end_quote]
                        date = rest[end_quote+1:].strip()
                        add_task(desc, date)
                    else:
                        print("Invalid quotes in description.")
                else:
                    parts = rest.split(None, 1)
                    if len(parts) == 2:
                        add_task(parts[0], parts[1])
                    else:
                        print("Invalid add command format. Use: add \"description\" due_date")
            elif line.lower().startswith("complete "):
                try:
                    tid = int(line[9:].strip())
                    complete_task(tid)
                except ValueError:
                    print("Invalid task ID.")
            elif line.lower().startswith("delete "):
                try:
                    tid = int(line[7:].strip())
                    delete_task(tid)
                except ValueError:
                    print("Invalid task ID.")
            else:
                print("Unknown command. Type 'help' for instructions.")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()
