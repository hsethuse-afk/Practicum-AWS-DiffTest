from taskmanager import TaskManager
from datetime import datetime, timedelta


def main():
    manager = TaskManager()

    print("=== Task Manager Demo ===\n")

    manager.add_task("Write project documentation", priority=2, category="work")
    manager.add_task("Buy groceries", priority=4, category="personal")
    manager.add_task("Fix critical bug", priority=1, category="work")
    manager.add_task("Call dentist", priority=3, category="personal")
    manager.add_task("Review pull requests", priority=2, category="work")

    deadline = datetime.now() + timedelta(days=2)
    manager.add_task("Submit report", priority=1, category="work", deadline=deadline)

    print("All tasks:")
    for task in manager.tasks:
        print(f"  {task}")

    print("\nTasks sorted by priority:")
    sorted_tasks = manager.get_sorted_tasks(by_priority=True)
    for task in sorted_tasks:
        print(f"  {task}")

    print("\nWork category tasks:")
    work_tasks = manager.get_tasks_by_category("work")
    for task in work_tasks:
        print(f"  {task}")

    manager.tasks[0].mark_complete()
    manager.tasks[2].mark_complete()

    print("\nStats:")
    stats = manager.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
