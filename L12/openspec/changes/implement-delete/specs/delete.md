# Specification: Delete Task with Archiving

This specification details the behavior of the `delete` command in the CLI task manager, which moves deleted tasks to `archive.json` rather than discarding them.

## Scenarios

### Scenario 1: Deleting an existing task successfully
* **Given** `tasks.json` contains:
  ```json
  [
    {
      "id": 1,
      "description": "Submit homework",
      "status": "pending",
      "priority": "high"
    }
  ]
  ```
* **And** `archive.json` is empty or does not exist
* **When** I run `python cli.py delete 1`
* **Then** the exit code is `0`
* **And** `tasks.json` is empty:
  ```json
  []
  ```
* **And** `archive.json` contains:
  ```json
  [
    {
      "id": 1,
      "description": "Submit homework",
      "status": "pending",
      "priority": "high",
      "deleted_at": "..."
    }
  ]
  ```
* **And** stdout contains "Archived task 1."

---

### Scenario 2: Deleting a nonexistent task returns an error
* **Given** `tasks.json` is empty
* **When** I run `python cli.py delete 99`
* **Then** the exit code is `1`
* **And** `tasks.json` remains empty
* **And** `archive.json` remains empty or does not exist
* **And** stderr contains "Error: Task with ID 99 not found."

---

### Scenario 3: Task listing prioritisation
* **Given** `tasks.json` contains:
  ```json
  [
    {"id": 1, "description": "Low task", "priority": "low"},
    {"id": 2, "description": "High task", "priority": "high"},
    {"id": 3, "description": "Medium task", "priority": "medium"}
  ]
  ```
* **When** I run `python cli.py list`
* **Then** the output displays the High task first, then the Medium task, and lastly the Low task.
