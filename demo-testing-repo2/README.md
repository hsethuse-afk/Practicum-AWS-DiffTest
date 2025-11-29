# Task Manager

A simple task management library for organizing and prioritizing tasks.

## Features

- Create tasks with priorities, categories, and deadlines
- Sort tasks by priority or title
- Track completed and pending tasks
- Identify overdue tasks
- Save and load tasks from JSON storage

## Project Structure

```
taskmanager/
├── __init__.py
├── task.py         # Task model
├── manager.py      # TaskManager with sorting
└── storage.py      # File storage utilities

tests/
└── test_manager.py # Unit tests

main.py             # Demo script
```

## Usage

Run the demo:
```bash
python main.py
```

Run tests:
```bash
python tests/test_manager.py
```

## Target Function for Testing

The `TaskManager.get_sorted_tasks()` method is the main target for differential testing:
- Located in `taskmanager/manager.py`
- Implements bubble sort algorithm
- Sorts tasks by priority or title
- Supports reverse sorting
