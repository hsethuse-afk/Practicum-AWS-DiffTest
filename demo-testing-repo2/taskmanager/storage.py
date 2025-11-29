import json
import os
from datetime import datetime


class Storage:
    def __init__(self, filepath="tasks.json"):
        self.filepath = filepath

    def save_tasks(self, tasks):
        tasks_data = [task.to_dict() for task in tasks]
        with open(self.filepath, 'w') as f:
            json.dump(tasks_data, f, indent=2)
        return True

    def load_tasks(self):
        if not os.path.exists(self.filepath):
            return []

        with open(self.filepath, 'r') as f:
            tasks_data = json.load(f)

        from .task import Task
        tasks = []
        for data in tasks_data:
            task = Task(
                title=data['title'],
                priority=data['priority'],
                category=data['category']
            )
            if data['deadline']:
                task.deadline = datetime.fromisoformat(data['deadline'])
            task.created_at = datetime.fromisoformat(data['created_at'])
            task.completed = data['completed']
            tasks.append(task)

        return tasks

    def clear(self):
        if os.path.exists(self.filepath):
            os.remove(self.filepath)
        return True
