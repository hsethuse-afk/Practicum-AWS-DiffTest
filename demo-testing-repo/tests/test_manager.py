import unittest
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from taskmanager import Task, TaskManager


class TestTaskManager(unittest.TestCase):
    def setUp(self):
        self.manager = TaskManager()

    def tearDown(self):
        self.manager.clear_all()

    def test_add_task(self):
        task = self.manager.add_task("Buy groceries", priority=2, category="shopping")
        self.assertEqual(task.title, "Buy groceries")
        self.assertEqual(task.priority, 2)
        self.assertEqual(len(self.manager.tasks), 1)

    def test_remove_task(self):
        task = self.manager.add_task("Test task")
        result = self.manager.remove_task(task)
        self.assertTrue(result)
        self.assertEqual(len(self.manager.tasks), 0)

    def test_get_sorted_tasks_by_priority(self):
        self.manager.add_task("Low priority task", priority=5)
        self.manager.add_task("High priority task", priority=1)
        self.manager.add_task("Medium priority task", priority=3)
        self.manager.add_task("Another high priority", priority=2)

        sorted_tasks = self.manager.get_sorted_tasks(by_priority=True, reverse=False)

        self.assertEqual(len(sorted_tasks), 4)
        self.assertEqual(sorted_tasks[0].priority, 1)
        self.assertEqual(sorted_tasks[1].priority, 2)
        self.assertEqual(sorted_tasks[2].priority, 3)
        self.assertEqual(sorted_tasks[3].priority, 5)

    def test_get_sorted_tasks_by_priority_reverse(self):
        self.manager.add_task("Low priority task", priority=5)
        self.manager.add_task("High priority task", priority=1)
        self.manager.add_task("Medium priority task", priority=3)

        sorted_tasks = self.manager.get_sorted_tasks(by_priority=True, reverse=True)

        self.assertEqual(sorted_tasks[0].priority, 5)
        self.assertEqual(sorted_tasks[1].priority, 3)
        self.assertEqual(sorted_tasks[2].priority, 1)

    def test_get_sorted_tasks_by_title(self):
        self.manager.add_task("Zebra task", priority=1)
        self.manager.add_task("Apple task", priority=2)
        self.manager.add_task("Mango task", priority=3)

        sorted_tasks = self.manager.get_sorted_tasks(by_priority=False, reverse=False)

        self.assertEqual(sorted_tasks[0].title, "Apple task")
        self.assertEqual(sorted_tasks[1].title, "Mango task")
        self.assertEqual(sorted_tasks[2].title, "Zebra task")

    def test_get_sorted_tasks_empty(self):
        sorted_tasks = self.manager.get_sorted_tasks()
        self.assertEqual(len(sorted_tasks), 0)

    def test_get_sorted_tasks_single(self):
        self.manager.add_task("Single task", priority=3)
        sorted_tasks = self.manager.get_sorted_tasks()
        self.assertEqual(len(sorted_tasks), 1)
        self.assertEqual(sorted_tasks[0].title, "Single task")

    def test_get_tasks_by_category(self):
        self.manager.add_task("Buy milk", category="shopping")
        self.manager.add_task("Write code", category="work")
        self.manager.add_task("Buy bread", category="shopping")

        shopping_tasks = self.manager.get_tasks_by_category("shopping")
        self.assertEqual(len(shopping_tasks), 2)

    def test_get_pending_tasks(self):
        task1 = self.manager.add_task("Task 1")
        task2 = self.manager.add_task("Task 2")
        task1.mark_complete()

        pending = self.manager.get_pending_tasks()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].title, "Task 2")

    def test_get_completed_tasks(self):
        task1 = self.manager.add_task("Task 1")
        task2 = self.manager.add_task("Task 2")
        task1.mark_complete()

        completed = self.manager.get_completed_tasks()
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].title, "Task 1")

    def test_get_overdue_tasks(self):
        past_deadline = datetime.now() - timedelta(days=1)
        future_deadline = datetime.now() + timedelta(days=1)

        self.manager.add_task("Overdue task", deadline=past_deadline)
        self.manager.add_task("Future task", deadline=future_deadline)

        overdue = self.manager.get_overdue_tasks()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].title, "Overdue task")

    def test_get_stats(self):
        task1 = self.manager.add_task("Task 1")
        task2 = self.manager.add_task("Task 2")
        past_deadline = datetime.now() - timedelta(days=1)
        self.manager.add_task("Overdue task", deadline=past_deadline)
        task1.mark_complete()

        stats = self.manager.get_stats()
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['completed'], 1)
        self.assertEqual(stats['pending'], 2)
        self.assertEqual(stats['overdue'], 1)


if __name__ == '__main__':
    unittest.main()
