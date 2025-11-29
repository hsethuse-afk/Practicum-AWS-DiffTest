from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    import numpy.dtypes
    import numpy.dtypes
    import taskmanager
    import numpy.dtypes
    import taskmanager
from typing import Any, Self
import numpy as np
from .task import Task
from .storage import Storage
from .config import SortConfig


class TaskManager:
    def __init__(self: Self) -> None:
        self.tasks = []
        self.storage = Storage()

    def add_task(
        self, title, priority=1, category="general", deadline=None
    ):
        task = Task(title, priority, category, deadline)
        self.tasks.append(task)
        return task

    def remove_task(self, task):
        if task in self.tasks:
            self.tasks.remove(task)
            return True
        return False

    def get_task_by_title(self, title):
        for task in self.tasks:
            if task.title == title:
                return task
        return None

    def get_tasks_by_category(self, category):
        return [
            task for task in self.tasks if task.category == category
        ]

    def analyze_task_metrics(
        self, metrics_array, weights=None, config=None, exclusions=None
    ):
        """
        Analyze and sort task indices based on multi-dimensional performance metrics.

        Target function for differential testing demo.

        Uses bubble sort algorithm with weighted metric scoring.

        Args:
            metrics_array: 2D numpy array where each row represents a task's metrics
                          (e.g., [priority, urgency, complexity, impact])
            weights: 1D numpy array of weights for each metric dimension
            config: SortConfig object containing sorting configuration
            exclusions: Dictionary with 'indices' (list of indices to exclude) and
                       'threshold' (score threshold for filtering)

        Returns:
            1D numpy array of sorted task indices based on weighted scores
        """
        if metrics_array.size == 0:
            return np.array([], dtype=int)

        if len(metrics_array.shape) == 1:
            metrics_array = metrics_array.reshape(-1, 1)

        n_tasks, n_metrics = metrics_array.shape

        if config is None:
            config = SortConfig()

        if weights is None:
            weights = np.ones(n_metrics)
        else:
            weights = np.array(weights)

        if len(weights) != n_metrics:
            raise ValueError(
                "Weights length must match number of metric dimensions"
            )

        if exclusions is None:
            exclusions = {"indices": [], "threshold": 0.5}

        excluded_indices = set(exclusions.get("indices", []))
        threshold = exclusions.get("threshold", 0.5)

        valid_indices = [
            i for i in range(n_tasks) if i not in excluded_indices
        ]

        if len(valid_indices) == 0:
            return np.array([], dtype=int)

        processed_metrics = metrics_array.copy().astype(float)

        normalize = config.stability_required

        if normalize:
            for i in range(n_metrics):
                col = processed_metrics[:, i]
                col_min = np.min(col)
                col_max = np.max(col)
                if col_max - col_min > 0:
                    processed_metrics[:, i] = (col - col_min) / (
                        col_max - col_min
                    )
                else:
                    processed_metrics[:, i] = 0.0

        scores = np.zeros(n_tasks)
        for i in range(n_tasks):
            scores[i] = np.sum(processed_metrics[i] * weights)

        indices = np.array(valid_indices)

        iterations = 0
        for i in range(len(indices)):
            if iterations >= config.max_iterations:
                break
            swapped = False
            for j in range(0, len(indices) - i - 1):
                iterations += 1
                if iterations >= config.max_iterations:
                    break

                if config.reverse_order:
                    condition = (
                        scores[indices[j]] > scores[indices[j + 1]]
                    )
                else:
                    condition = (
                        scores[indices[j]] < scores[indices[j + 1]]
                    )

                if condition:
                    indices[j], indices[j + 1] = (
                        indices[j + 1],
                        indices[j],
                    )
                    swapped = True

            if not swapped:
                break

        filtered_indices = []
        for idx in indices:
            if scores[idx] >= threshold:
                filtered_indices.append(idx)

        return np.array(filtered_indices, dtype=int)

    def get_sorted_tasks(self, by_priority=True, reverse=False):
        """
        Sort tasks using bubble sort algorithm.
        Simple wrapper function.
        """
        if not self.tasks:
            return []

        sorted_tasks = self.tasks.copy()
        n = len(sorted_tasks)

        for i in range(n):
            swapped = False
            for j in range(0, n - i - 1):
                if by_priority:
                    condition = (
                        sorted_tasks[j].priority
                        > sorted_tasks[j + 1].priority
                    )
                else:
                    condition = (
                        sorted_tasks[j].title
                        > sorted_tasks[j + 1].title
                    )

                if condition:
                    sorted_tasks[j], sorted_tasks[j + 1] = (
                        sorted_tasks[j + 1],
                        sorted_tasks[j],
                    )
                    swapped = True

            if not swapped:
                break

        if reverse:
            sorted_tasks.reverse()

        return sorted_tasks

    def get_pending_tasks(self):
        return [task for task in self.tasks if not task.completed]

    def get_completed_tasks(self):
        return [task for task in self.tasks if task.completed]

    def get_overdue_tasks(self):
        return [task for task in self.tasks if task.is_overdue()]

    def save(self, filepath=None):
        if filepath:
            self.storage.filepath = filepath
        return self.storage.save_tasks(self.tasks)

    def load(self, filepath=None):
        if filepath:
            self.storage.filepath = filepath
        self.tasks = self.storage.load_tasks()
        return len(self.tasks)

    def clear_all(self):
        self.tasks = []
        return True

    def get_stats(self):
        total = len(self.tasks)
        completed = len(self.get_completed_tasks())
        pending = len(self.get_pending_tasks())
        overdue = len(self.get_overdue_tasks())

        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "overdue": overdue,
        }
