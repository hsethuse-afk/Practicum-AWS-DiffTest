import numpy as np
from taskmanager import TaskManager, SortConfig


def main():
    manager = TaskManager()

    print("=== Task Metrics Analysis Demo ===\n")

    print("Scenario 1: Basic task prioritization")
    print("Tasks with [priority, urgency, complexity, impact] metrics:\n")

    metrics = np.array([
        [5, 3, 7, 2],
        [3, 5, 2, 8],
        [4, 4, 5, 5],
        [5, 5, 5, 5],
        [1, 2, 1, 1]
    ])

    task_names = [
        "Fix critical bug",
        "Customer feature request",
        "Code refactoring",
        "Security update",
        "Documentation typo"
    ]

    print("Task metrics:")
    for i, (name, metric) in enumerate(zip(task_names, metrics)):
        print(f"  Task {i}: {name}")
        print(f"    Metrics: {metric}")

    exclusions = {'indices': [], 'threshold': 0.3}
    result = manager.analyze_task_metrics(metrics, exclusions=exclusions)

    print(f"\nSorted task indices (threshold=0.3): {result}")
    print("Sorted tasks:")
    for idx in result:
        print(f"  {idx}: {task_names[idx]}")

    print("\n" + "=" * 50 + "\n")
    print("Scenario 2: Weighted prioritization with custom config")
    print("Priority matters more than other factors\n")

    weights = np.array([0.5, 0.3, 0.1, 0.1])
    config = SortConfig(algorithm="bubble", reverse_order=False, stability_required=True)
    exclusions = {'indices': [], 'threshold': 0.2}

    result_weighted = manager.analyze_task_metrics(
        metrics,
        weights=weights,
        config=config,
        exclusions=exclusions
    )

    print(f"Config: {config}")
    print(f"Weights: {weights}")
    print(f"Sorted indices: {result_weighted}")
    print("Sorted tasks:")
    for idx in result_weighted:
        print(f"  {idx}: {task_names[idx]}")

    print("\n" + "=" * 50 + "\n")
    print("Scenario 3: Excluding specific tasks")
    print("Exclude task 1 (Customer feature request) from analysis:\n")

    exclusions_with_skips = {'indices': [1, 4], 'threshold': 0.2}
    result_excluded = manager.analyze_task_metrics(
        metrics,
        weights=weights,
        exclusions=exclusions_with_skips
    )

    print(f"Excluded indices: {exclusions_with_skips['indices']}")
    print(f"Sorted indices: {result_excluded}")
    print("Remaining sorted tasks:")
    for idx in result_excluded:
        print(f"  {idx}: {task_names[idx]}")

    print("\n" + "=" * 50 + "\n")
    print("Scenario 4: Reverse order sorting")
    print("Sort from lowest to highest priority:\n")

    config_reverse = SortConfig(reverse_order=True, stability_required=True)
    exclusions = {'indices': [], 'threshold': 0.0}

    result_reverse = manager.analyze_task_metrics(
        metrics,
        config=config_reverse,
        exclusions=exclusions
    )

    print(f"Config: {config_reverse}")
    print(f"Sorted indices (reverse): {result_reverse}")
    print("Sorted tasks (lowest priority first):")
    for idx in result_reverse:
        print(f"  {idx}: {task_names[idx]}")

    print("\n" + "=" * 50 + "\n")
    print("Scenario 5: Complex scenario with all parameters")
    print("Using custom config, weights, and exclusions:\n")

    large_metrics = np.random.rand(20, 4) * 10

    config_complex = SortConfig(algorithm="bubble", stability_required=True)
    config_complex.set_max_iterations(500)
    weights_complex = np.array([0.4, 0.3, 0.2, 0.1])
    exclusions_complex = {'indices': [5, 10, 15], 'threshold': 0.6}

    result_complex = manager.analyze_task_metrics(
        large_metrics,
        weights=weights_complex,
        config=config_complex,
        exclusions=exclusions_complex
    )

    print(f"Total tasks: 20")
    print(f"Excluded indices: {exclusions_complex['indices']}")
    print(f"Threshold: {exclusions_complex['threshold']}")
    print(f"Tasks passing all filters: {len(result_complex)}")
    print(f"Top 5 task indices: {result_complex[:5]}")


if __name__ == "__main__":
    main()
