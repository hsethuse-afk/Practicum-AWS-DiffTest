from datetime import datetime


class Task:
    def __init__(self, title, priority=1, category="general", deadline=None):
        self.title = title
        self.priority = priority
        self.category = category
        self.deadline = deadline
        self.created_at = datetime.now()
        self.completed = False

    def mark_complete(self):
        self.completed = True
        return self

    def update_priority(self, new_priority):
        if new_priority < 1 or new_priority > 5:
            raise ValueError("Priority must be between 1 and 5")
        self.priority = new_priority
        return self

    def is_overdue(self):
        if self.deadline is None:
            return False
        return datetime.now() > self.deadline and not self.completed

    def to_dict(self):
        return {
            'title': self.title,
            'priority': self.priority,
            'category': self.category,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'created_at': self.created_at.isoformat(),
            'completed': self.completed
        }

    def __repr__(self):
        status = "✓" if self.completed else "○"
        return f"{status} [{self.priority}] {self.title} ({self.category})"
