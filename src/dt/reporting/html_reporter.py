"""HTML report generator for differential testing results."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..contracts import TestResult, RunConfig, StrategyPlan, RunResult
from ..results import ResultCollector
from ..logger import get_logger


class HTMLReporter:
    """
    Generates interactive HTML reports for differential testing results.

    The report includes:
    - Executive summary with stats
    - Test configuration (strategy JSON)
    - Detailed mismatch table (filterable, searchable)
    - Matching results (collapsed by default)
    - Instance distribution (for class methods)
    - Warnings section
    - Reproduction metadata
    """

    def __init__(self):
        self.log = get_logger()

        # Set up Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(exist_ok=True)

        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def generate_report(
        self,
        test_result: TestResult,
        a_results: List[RunResult],
        b_results: List[RunResult],
        strategy: StrategyPlan,
        config: RunConfig,
        command: str,
        duration: float,
        output_path: str
    ) -> str:
        """
        Generate an HTML report from test results.

        Args:
            test_result: The test result object
            a_results: Results from version A
            b_results: Results from version B
            strategy: The strategy used for testing
            config: Run configuration
            command: Command line used to run the test
            duration: Test duration in seconds
            output_path: Path to save the HTML report

        Returns:
            Path to the generated report
        """
        self.log.verbose(f"[HTMLReporter] Generating HTML report: {output_path}")

        # Prepare data for template
        context = self._prepare_context(
            test_result, a_results, b_results, strategy, config, command, duration
        )

        # Render template
        template = self.env.get_template('report.html')
        html_content = template.render(**context)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        self.log.verbose(f"[HTMLReporter] Report saved to: {output_path}")
        return output_path

    def _prepare_context(
        self,
        test_result: TestResult,
        a_results: List[RunResult],
        b_results: List[RunResult],
        strategy: StrategyPlan,
        config: RunConfig,
        command: str,
        duration: float
    ) -> Dict[str, Any]:
        """Prepare template context from test data."""

        target = test_result.target
        detail = test_result.detail
        stats = detail.get('stats', {})

        # Calculate match rate
        total = stats.get('total_examples', 0)
        matches = stats.get('successes', 0)
        match_rate = (matches / total * 100) if total > 0 else 0

        # Get complete lists from comparator
        mismatches_list = detail.get('mismatches', [])
        matches_list = detail.get('matches', [])

        # Format for display
        mismatches_formatted = self._format_results(
            mismatches_list, target.is_class_method, is_mismatch=True
        )

        matches_formatted = self._format_results(
            matches_list, target.is_class_method, is_mismatch=False
        )

        # Prepare instance statistics (for class methods)
        instance_stats = None
        if target.is_class_method:
            instance_stats = self._calculate_instance_stats(
                mismatches_formatted, matches_formatted
            )

        # Serialize strategy to JSON
        strategy_json = self._serialize_strategy(strategy)

        # Build context
        context = {
            # Test metadata
            'function_name': target.func_name,
            'class_name': target.class_name,
            'file_a': target.file_a,
            'file_b': target.file_b,
            'is_class_method': target.is_class_method,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'duration': f"{duration:.2f}",
            'command': command,

            # Statistics
            'stats': {
                'total': total,
                'mismatches': stats.get('mismatches', 0),
                'successes': matches,
                'match_rate': f"{match_rate:.1f}",
            },

            # Results
            'mismatches': mismatches_formatted,
            'matches': matches_formatted,
            'instance_stats': instance_stats,

            # Configuration
            'strategy_json': strategy_json,
            'max_examples': config.max_examples,
            'seed': config.seed,

            # Warnings
            'warnings': test_result.warnings or [],

            # Status
            'passed': test_result.passed,
        }

        return context

    def _format_results(
        self,
        results: List[Dict[str, Any]],
        is_class_method: bool,
        is_mismatch: bool
    ) -> List[Dict[str, Any]]:
        """Format results for display in the report."""
        formatted = []

        for idx, result in enumerate(results, 1):
            args = result.get('args', ())
            if is_mismatch:
                output_a = result.get('A')
                output_b = result.get('B')
            else:
                # For matches, both outputs are the same
                output_a = result.get('output')
                output_b = result.get('output')

            # Format arguments
            args_formatted = ResultCollector._format_args(args, is_class_method)

            # Extract instance info (for class methods)
            instance_repr = None
            instance_id = None
            if is_class_method and args:
                instance = args[0]
                instance_repr = ResultCollector._format_instance(instance)
                instance_id = id(instance)

            # Format outputs
            output_a_str = self._format_output(output_a)
            output_b_str = self._format_output(output_b)

            formatted.append({
                'index': idx,
                'args_formatted': args_formatted,
                'instance_repr': instance_repr,
                'instance_id': instance_id,
                'output_a': output_a_str,
                'output_b': output_b_str,
                'output_a_raw': output_a,
                'output_b_raw': output_b,
            })

        return formatted

    def _extract_matches(
        self,
        a_results: List[RunResult],
        b_results: List[RunResult],
        mismatches: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract matching results from full result sets."""
        # The comparator only includes actual mismatches in the mismatches list
        # So the number of matches = total - number of mismatches
        # We can determine matches by comparing outputs directly

        matches = []
        for idx, (a_res, b_res) in enumerate(zip(a_results, b_results)):
            # Check if outputs match
            if self._outputs_equal(a_res.output, b_res.output):
                matches.append({
                    'args': a_res.input,
                    'output_a': a_res.output,
                    'output_b': b_res.output,
                })

        return matches

    def _outputs_equal(self, output_a: Any, output_b: Any) -> bool:
        """Check if two outputs are equal (handles NumPy arrays and other special types)."""
        try:
            import numpy as np
            if isinstance(output_a, np.ndarray) and isinstance(output_b, np.ndarray):
                return np.array_equal(output_a, output_b)
        except ImportError:
            pass

        try:
            return output_a == output_b
        except:
            return False

    def _calculate_instance_stats(
        self,
        mismatches: List[Dict[str, Any]],
        matches: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate per-instance statistics for class methods."""
        instance_map = {}

        # Count mismatches per instance
        for mm in mismatches:
            inst_id = mm['instance_id']
            if inst_id not in instance_map:
                instance_map[inst_id] = {
                    'repr': mm['instance_repr'],
                    'id': inst_id,
                    'mismatches': 0,
                    'matches': 0,
                }
            instance_map[inst_id]['mismatches'] += 1

        # Count matches per instance
        for match in matches:
            inst_id = match.get('instance_id')
            if inst_id:
                if inst_id not in instance_map:
                    instance_map[inst_id] = {
                        'repr': match['instance_repr'],
                        'id': inst_id,
                        'mismatches': 0,
                        'matches': 0,
                    }
                instance_map[inst_id]['matches'] += 1

        # Calculate rates
        stats = []
        for inst_data in instance_map.values():
            total = inst_data['mismatches'] + inst_data['matches']
            mismatch_rate = (inst_data['mismatches'] / total * 100) if total > 0 else 0

            stats.append({
                'repr': inst_data['repr'],
                'id': inst_data['id'],
                'total': total,
                'mismatches': inst_data['mismatches'],
                'matches': inst_data['matches'],
                'mismatch_rate': f"{mismatch_rate:.1f}",
            })

        # Sort by number of mismatches (descending)
        stats.sort(key=lambda x: x['mismatches'], reverse=True)

        return stats

    def _format_output(self, output: Any) -> str:
        """Format output value for display."""
        if isinstance(output, tuple) and len(output) == 2 and output[0] in ('ret', 'exc'):
            status, value = output
            if status == 'ret':
                return f"<span class='output-status return'>Return:</span> {self._escape_html(repr(value))}"
            else:
                return f"<span class='output-status exception'>Exception:</span> {self._escape_html(str(value))}"
        return self._escape_html(repr(output))

    def _serialize_strategy(self, strategy: StrategyPlan) -> str:
        """Serialize strategy plan to formatted JSON."""
        # This is a simplified version - in practice you'd use the strategy serializer
        strategy_dict = {
            'arg_strategy': repr(strategy.arg_strategy),
            'num_instances': strategy.num_instances,
        }
        return json.dumps(strategy_dict, indent=2)

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
