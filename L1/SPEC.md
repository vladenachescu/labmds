# Technical Specification: Command-Line TODO List Application

This document defines the requirements and behavior for the interactive CLI TODO list manager.

## 1. Functional Requirements

The application must run in an interactive Read-Eval-Print Loop (REPL) and support the following commands:

### 1.1 Add Task
* **Command Syntax**: `add "<description>" <due_date>`
* **Description**: Adds a new task to the list. Tasks must be assigned a unique incrementing integer ID starting from 1. 
* **State**: Newly created tasks default to a `pending` status.
* **Storage**: Persistent in `tasks.json`.

### 1.2 Complete Task
* **Command Syntax**: `complete <id>`
* **Description**: Marks the task with the given ID as `complete`.
* **Errors**: If the ID does not exist, display an appropriate error message.

### 1.3 Delete Task
* **Command Syntax**: `delete <id>`
* **Description**: Deletes the task with the given ID from the list.
* **Errors**: If the ID does not exist, display an error message.

### 1.4 List Tasks
* **Command Syntax**: `list`
* **Description**: Prints all tasks currently in the database, displaying their ID, status (marked as `[ ]` for pending, `[X]` for complete), description, and due date.

### 1.5 Help
* **Command Syntax**: `help`
* **Description**: Prints a list of all available commands and their syntax.

### 1.6 Exit
* **Command Syntax**: `exit` or `quit`
* **Description**: Safely terminates the interactive session.

---

## 2. Technical Stack & Architecture

- **Language**: Python 3
- **Data Persistence**: JSON file storage (`tasks.json`) loaded and saved atomically on every modifying operation to ensure consistency.
- **Interface**: Shell-based command-line interface with persistent prompt prefix `todo> `.
