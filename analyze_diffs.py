#!/usr/bin/env python3
"""
Analyze extracted diffs to find meaningful code changes for differential testing.
Filters out trivial changes (version bumps, docs, etc.) and identifies
function-level changes suitable for type inference testing.
"""

import json
from pathlib import Path
from typing import Dict, List
import ast


class DiffAnalyzer:
    def __init__(self, diffs_file: str = "diff_test_data/extracted_diffs.json"):
        self.diffs_file = Path(diffs_file)
        self.diffs = self.load_diffs()

    def load_diffs(self) -> List[Dict]:
        """Load the extracted diffs from JSON."""
        with open(self.diffs_file) as f:
            return json.load(f)

    def is_trivial_change(self, diff_data: Dict) -> bool:
        """Check if a diff is trivial (version bumps, formatting, etc.)."""
        diff_text = diff_data['diff']
        filepath = diff_data['file']

        # Skip documentation files
        if any(x in filepath.lower() for x in ['docs/', 'doc/', 'readme', 'changelog', 'history']):
            return True

        # Skip setup/config files
        if any(x in filepath for x in ['setup.py', 'conf.py', '__init__.py']):
            # Check if it's just a version bump
            if '__version__' in diff_text or 'version =' in diff_text:
                # Count non-version changes
                lines = [l for l in diff_text.split('\n')
                        if l.startswith(('+', '-')) and not l.startswith(('+++', '---'))]
                non_version_lines = [l for l in lines
                                    if 'version' not in l.lower() and 'release' not in l.lower()]
                if len(non_version_lines) < 3:
                    return True

        # Skip test files for now (we want source code changes)
        if 'test_' in filepath or '/tests/' in filepath or '/test/' in filepath:
            return True

        # Check diff size - skip very small changes
        added_lines = len([l for l in diff_text.split('\n') if l.startswith('+')])
        removed_lines = len([l for l in diff_text.split('\n') if l.startswith('-')])
        if added_lines + removed_lines < 5:
            return True

        return False

    def extract_changed_functions(self, diff_data: Dict) -> List[Dict]:
        """Extract information about functions that were changed."""
        before_code = diff_data['before']
        after_code = diff_data['after']

        changed_functions = []

        try:
            before_tree = ast.parse(before_code)
            after_tree = ast.parse(after_code)

            before_funcs = self.get_functions_from_ast(before_tree)
            after_funcs = self.get_functions_from_ast(after_tree)

            # Find functions that exist in both versions
            common_funcs = set(before_funcs.keys()) & set(after_funcs.keys())

            for func_name in common_funcs:
                before_func = before_funcs[func_name]
                after_func = after_funcs[func_name]

                # Check if the function actually changed
                if before_func['source'] != after_func['source']:
                    changed_functions.append({
                        'name': func_name,
                        'before': before_func,
                        'after': after_func,
                        'has_type_hints_before': before_func['has_annotations'],
                        'has_type_hints_after': after_func['has_annotations']
                    })

        except SyntaxError:
            # Skip files with syntax errors
            pass

        return changed_functions

    def get_functions_from_ast(self, tree: ast.AST) -> Dict[str, Dict]:
        """Extract all function definitions from an AST."""
        functions = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                try:
                    source = ast.unparse(node)
                except:
                    source = ""

                func_info = {
                    'name': node.name,
                    'lineno': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'has_annotations': self.has_type_annotations(node),
                    'source': source
                }
                functions[node.name] = func_info

        return functions

    def has_type_annotations(self, func_node: ast.FunctionDef) -> bool:
        """Check if a function has type annotations."""
        # Check return annotation
        if func_node.returns:
            return True

        # Check argument annotations
        for arg in func_node.args.args:
            if arg.annotation:
                return True

        return False

    def categorize_diffs(self) -> Dict[str, List[Dict]]:
        """Categorize diffs into different types."""
        categories = {
            'trivial': [],
            'function_changes_no_types': [],
            'function_changes_with_types': [],
            'new_functions': [],
            'complex_changes': []
        }

        for diff_data in self.diffs:
            if self.is_trivial_change(diff_data):
                categories['trivial'].append(diff_data)
                continue

            changed_funcs = self.extract_changed_functions(diff_data)

            if not changed_funcs:
                categories['complex_changes'].append(diff_data)
                continue

            # Categorize based on type hints
            has_types_before = any(f['has_type_hints_before'] for f in changed_funcs)
            has_types_after = any(f['has_type_hints_after'] for f in changed_funcs)

            enriched_diff = diff_data.copy()
            enriched_diff['changed_functions'] = changed_funcs

            if has_types_before or has_types_after:
                categories['function_changes_with_types'].append(enriched_diff)
            else:
                categories['function_changes_no_types'].append(enriched_diff)

        return categories

    def generate_report(self, categories: Dict[str, List[Dict]]) -> str:
        """Generate a summary report of the analysis."""
        report = []
        report.append("=" * 80)
        report.append("DIFF ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"\nTotal diffs analyzed: {len(self.diffs)}\n")

        for category, diffs in categories.items():
            report.append(f"\n{category.upper().replace('_', ' ')}: {len(diffs)}")

            if category not in ['trivial'] and diffs:
                report.append("-" * 40)
                for i, diff in enumerate(diffs[:5], 1):  # Show first 5
                    report.append(f"  {i}. {diff['project']}: {diff['file']}")
                    if 'changed_functions' in diff:
                        func_names = [f['name'] for f in diff['changed_functions']]
                        report.append(f"     Functions: {', '.join(func_names[:3])}")
                if len(diffs) > 5:
                    report.append(f"  ... and {len(diffs) - 5} more")

        report.append("\n" + "=" * 80)
        report.append("RECOMMENDATIONS FOR DIFFERENTIAL TESTING")
        report.append("=" * 80)

        # Recommend best candidates
        best_candidates = categories['function_changes_no_types']
        report.append(f"\nBest candidates (function changes without type hints): {len(best_candidates)}")
        report.append("These are ideal for testing type inference tools.\n")

        return "\n".join(report)

    def save_categorized_diffs(self, categories: Dict[str, List[Dict]],
                               output_dir: str = "diff_test_data/categorized"):
        """Save categorized diffs to separate files."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)

        for category, diffs in categories.items():
            output_file = output_path / f"{category}.json"
            with open(output_file, 'w') as f:
                json.dump(diffs, f, indent=2)

        print(f"\nCategorized diffs saved to: {output_path}")


def main():
    analyzer = DiffAnalyzer()

    print("Analyzing extracted diffs...")
    categories = analyzer.categorize_diffs()

    # Generate and display report
    report = analyzer.generate_report(categories)
    print(report)

    # Save categorized diffs
    analyzer.save_categorized_diffs(categories)

    # Save report to file
    report_file = Path("diff_test_data/analysis_report.txt")
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\nReport saved to: {report_file}")


if __name__ == "__main__":
    main()
