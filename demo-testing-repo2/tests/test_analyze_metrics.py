import unittest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from taskmanager import TaskManager, SortConfig


class TestAnalyzeTaskMetrics(unittest.TestCase):
    def setUp(self):
        self.manager = TaskManager()

    def test_empty_array(self):
        result = self.manager.analyze_task_metrics(np.array([]))
        self.assertEqual(len(result), 0)
        self.assertEqual(result.dtype, np.int64)

    def test_single_task_single_metric(self):
        metrics = np.array([5.0])
        exclusions = {'indices': [], 'threshold': 0.0}
        result = self.manager.analyze_task_metrics(metrics, exclusions=exclusions)
        np.testing.assert_array_equal(result, np.array([0]))

    def test_single_task_multiple_metrics(self):
        metrics = np.array([[3.0, 4.0, 5.0]])
        config = SortConfig()
        exclusions = {'indices': [], 'threshold': 0.0}
        result = self.manager.analyze_task_metrics(metrics, config=config, exclusions=exclusions)
        np.testing.assert_array_equal(result, np.array([0]))

    def test_multiple_tasks_single_metric(self):
        metrics = np.array([3.0, 5.0, 1.0, 4.0])
        result = self.manager.analyze_task_metrics(metrics, exclusions={"indices": [], "threshold": 0.0})
        np.testing.assert_array_equal(result, np.array([1, 3, 0, 2]))

    def test_multiple_tasks_multiple_metrics_no_weights(self):
        metrics = np.array([
            [1.0, 2.0, 3.0],
            [3.0, 3.0, 3.0],
            [2.0, 1.0, 4.0],
            [5.0, 5.0, 5.0]
        ])
        result = self.manager.analyze_task_metrics(metrics, exclusions={"indices": [], "threshold": 0.0})
        expected = np.array([3, 1, 2, 0])
        np.testing.assert_array_equal(result, expected)

    def test_with_custom_weights(self):
        metrics = np.array([
            [1.0, 5.0],
            [5.0, 1.0],
            [3.0, 3.0]
        ])
        weights = np.array([2.0, 1.0])
        result = self.manager.analyze_task_metrics(metrics, weights=weights, exclusions={"indices": [], "threshold": 0.0})
        np.testing.assert_array_equal(result, np.array([1, 2, 0]))

    def test_with_threshold_filtering(self):
        metrics = np.array([
            [10.0, 10.0],
            [5.0, 5.0],
            [1.0, 1.0],
            [8.0, 8.0]
        ])
        exclusions = {'indices': [], 'threshold': 0.7}
        result = self.manager.analyze_task_metrics(metrics, exclusions=exclusions)
        self.assertTrue(0 in result)
        self.assertTrue(3 in result)
        self.assertFalse(2 in result)

    def test_normalization_enabled(self):
        metrics = np.array([
            [10.0, 100.0],
            [20.0, 200.0],
            [5.0, 50.0]
        ])
        config = SortConfig(stability_required=True)
        exclusions = {"indices": [], "threshold": 0.0}
        result = self.manager.analyze_task_metrics(metrics, config=config, exclusions=exclusions)
        np.testing.assert_array_equal(result, np.array([1, 0, 2]))

    def test_normalization_disabled(self):
        metrics = np.array([
            [1.0, 1.0],
            [2.0, 2.0],
            [3.0, 3.0]
        ])
        config = SortConfig(stability_required=False)
        exclusions = {"indices": [], "threshold": 0.0}
        result = self.manager.analyze_task_metrics(metrics, config=config, exclusions=exclusions)
        np.testing.assert_array_equal(result, np.array([2, 1, 0]))

    def test_identical_values(self):
        metrics = np.array([
            [5.0, 5.0],
            [5.0, 5.0],
            [5.0, 5.0]
        ])
        result = self.manager.analyze_task_metrics(metrics, exclusions={"indices": [], "threshold": 0.0})
        self.assertEqual(len(result), 3)

    def test_negative_values(self):
        metrics = np.array([
            [-5.0, 10.0],
            [5.0, -10.0],
            [0.0, 0.0]
        ])
        config = SortConfig(stability_required=True)
        exclusions = {"indices": [], "threshold": 0.0}
        result = self.manager.analyze_task_metrics(metrics, config=config, exclusions=exclusions)
        self.assertEqual(len(result), 3)

    def test_large_array(self):
        metrics = np.random.rand(100, 5)
        result = self.manager.analyze_task_metrics(metrics, exclusions={"indices": [], "threshold": 0.0})
        self.assertEqual(len(result), 100)
        self.assertTrue(np.all(result >= 0))
        self.assertTrue(np.all(result < 100))

    def test_mixed_positive_negative_weights(self):
        metrics = np.array([
            [10.0, 5.0],
            [5.0, 10.0],
            [7.0, 7.0]
        ])
        weights = np.array([1.0, -0.5])
        result = self.manager.analyze_task_metrics(metrics, weights=weights, exclusions={"indices": [], "threshold": 0.0})
        self.assertGreaterEqual(len(result), 0)
        self.assertLessEqual(len(result), 3)

    def test_zero_weights(self):
        metrics = np.array([
            [10.0, 5.0],
            [5.0, 10.0],
            [1.0, 1.0]
        ])
        weights = np.array([0.0, 0.0])
        result = self.manager.analyze_task_metrics(metrics, weights=weights, exclusions={"indices": [], "threshold": 0.0})
        self.assertEqual(len(result), 3)

    def test_high_threshold_filters_all(self):
        metrics = np.array([
            [1.0, 2.0],
            [3.0, 4.0],
            [5.0, 6.0]
        ])
        exclusions = {'indices': [], 'threshold': 10.0}
        result = self.manager.analyze_task_metrics(metrics, exclusions=exclusions)
        self.assertEqual(len(result), 0)

    def test_weights_length_mismatch_raises_error(self):
        metrics = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0]
        ])
        weights = np.array([1.0, 1.0])
        with self.assertRaises(ValueError):
            self.manager.analyze_task_metrics(metrics, weights=weights)

    def test_integer_input_arrays(self):
        metrics = np.array([
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9]
        ])
        result = self.manager.analyze_task_metrics(metrics, exclusions={"indices": [], "threshold": 0.0})
        self.assertEqual(result.dtype, np.int64)
        np.testing.assert_array_equal(result, np.array([2, 1, 0]))

    def test_varying_dimensions(self):
        metrics_2d = np.array([[1, 2], [3, 4]])
        result_2d = self.manager.analyze_task_metrics(metrics_2d, exclusions={"indices": [], "threshold": 0.0})
        self.assertEqual(len(result_2d), 2)

        metrics_4d = np.array([[1, 2, 3, 4], [5, 6, 7, 8]])
        result_4d = self.manager.analyze_task_metrics(metrics_4d, exclusions={"indices": [], "threshold": 0.0})
        self.assertEqual(len(result_4d), 2)

    def test_single_column_normalization(self):
        metrics = np.array([
            [5.0],
            [10.0],
            [15.0],
            [20.0]
        ])
        config = SortConfig(stability_required=True)
        exclusions = {"indices": [], "threshold": 0.0}
        result = self.manager.analyze_task_metrics(metrics, config=config, exclusions=exclusions)
        np.testing.assert_array_equal(result, np.array([3, 2, 1, 0]))

    def test_realistic_task_metrics(self):
        metrics = np.array([
            [5, 3, 7, 2],
            [3, 5, 2, 8],
            [4, 4, 5, 5],
            [5, 5, 5, 5]
        ])
        weights = np.array([0.4, 0.3, 0.2, 0.1])
        exclusions = {'indices': [], 'threshold': 0.3}
        result = self.manager.analyze_task_metrics(
            metrics,
            weights=weights,
            exclusions=exclusions
        )
        self.assertGreater(len(result), 0)
        self.assertLessEqual(len(result), 4)

    def test_with_custom_config_object(self):
        metrics = np.array([
            [1.0, 2.0],
            [3.0, 4.0],
            [5.0, 6.0]
        ])
        config = SortConfig(algorithm="bubble", reverse_order=False, stability_required=True)
        exclusions = {'indices': [], 'threshold': 0.0}
        result = self.manager.analyze_task_metrics(metrics, config=config, exclusions=exclusions)
        np.testing.assert_array_equal(result, np.array([2, 1, 0]))

    def test_with_reverse_order_config(self):
        metrics = np.array([
            [1.0, 2.0],
            [3.0, 4.0],
            [5.0, 6.0]
        ])
        config = SortConfig(reverse_order=True)
        exclusions = {'indices': [], 'threshold': 0.0}
        result = self.manager.analyze_task_metrics(metrics, config=config, exclusions=exclusions)
        np.testing.assert_array_equal(result, np.array([0, 1, 2]))

    def test_with_exclusions_dict(self):
        metrics = np.array([
            [10.0, 10.0],
            [5.0, 5.0],
            [8.0, 8.0],
            [3.0, 3.0]
        ])
        exclusions = {'indices': [1, 3], 'threshold': 0.0}
        result = self.manager.analyze_task_metrics(metrics, exclusions=exclusions)
        self.assertNotIn(1, result)
        self.assertNotIn(3, result)
        self.assertIn(0, result)
        self.assertIn(2, result)

    def test_with_exclusions_and_threshold(self):
        metrics = np.array([
            [10.0, 10.0],
            [5.0, 5.0],
            [8.0, 8.0],
            [3.0, 3.0],
            [1.0, 1.0]
        ])
        exclusions = {'indices': [1], 'threshold': 0.4}
        result = self.manager.analyze_task_metrics(metrics, exclusions=exclusions)
        self.assertNotIn(1, result)
        self.assertNotIn(4, result)
        self.assertTrue(len(result) > 0)

    def test_config_with_max_iterations(self):
        metrics = np.array([
            [5.0, 3.0],
            [2.0, 8.0],
            [7.0, 1.0],
            [4.0, 6.0]
        ])
        config = SortConfig()
        config.set_max_iterations(2)
        exclusions = {'indices': [], 'threshold': 0.0}
        result = self.manager.analyze_task_metrics(metrics, config=config, exclusions=exclusions)
        self.assertEqual(len(result), 4)

    def test_all_excluded(self):
        metrics = np.array([
            [1.0, 2.0],
            [3.0, 4.0],
            [5.0, 6.0]
        ])
        exclusions = {'indices': [0, 1, 2], 'threshold': 0.0}
        result = self.manager.analyze_task_metrics(metrics, exclusions=exclusions)
        self.assertEqual(len(result), 0)

    def test_complex_scenario_all_parameters(self):
        metrics = np.array([
            [5, 8, 3, 9],
            [7, 2, 6, 4],
            [1, 5, 8, 2],
            [9, 3, 4, 7],
            [6, 6, 5, 5]
        ])
        weights = np.array([0.3, 0.25, 0.25, 0.2])
        config = SortConfig(algorithm="bubble", reverse_order=False, stability_required=True)
        config.set_max_iterations(100)
        exclusions = {'indices': [2], 'threshold': 0.4}

        result = self.manager.analyze_task_metrics(
            metrics,
            weights=weights,
            config=config,
            exclusions=exclusions
        )

        self.assertNotIn(2, result)
        self.assertGreater(len(result), 0)
        for idx in result:
            self.assertIn(idx, [0, 1, 3, 4])

    def test_empty_exclusions_dict(self):
        metrics = np.array([[1.0, 2.0], [3.0, 4.0]])
        exclusions = {}
        result = self.manager.analyze_task_metrics(metrics, exclusions=exclusions)
        self.assertGreaterEqual(len(result), 0)
        self.assertLessEqual(len(result), 2)

    def test_config_without_normalization(self):
        metrics = np.array([
            [1.0, 100.0],
            [10.0, 10.0],
            [50.0, 50.0]
        ])
        config = SortConfig(stability_required=False)
        exclusions = {'indices': [], 'threshold': 0.0}
        result = self.manager.analyze_task_metrics(metrics, config=config, exclusions=exclusions)
        self.assertEqual(len(result), 3)


if __name__ == '__main__':
    unittest.main()
