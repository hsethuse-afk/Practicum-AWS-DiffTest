#!/usr/bin/env python3
"""
Generate test cases from categorized diffs for differential testing.
Creates before/after test files and metadata for running type inference tools.
"""

import json
from pathlib import Path
from typing import Dict, List
import hashlib


class TestCaseGenerator:
    def __init__(self, output_dir: str = "diff_test_cases"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def load_categorized_diffs(self, category: str = "function_changes_no_types") -> List[Dict]:
        """Load diffs from a specific category."""
        category_file = Path(f"diff_test_data/categorized/{category}.json")
        with open(category_file) as f:
            return json.load(f)

    def create_test_id(self, diff_data: Dict) -> str:
        """Create a unique test case ID."""
        content = f"{diff_data['project']}_{diff_data['commit']}_{diff_data['file']}"
        hash_id = hashlib.md5(content.encode()).hexdigest()[:8]
        project_short = diff_data['project'].split('_')[-1]  # e.g., "grab" from "01_grab"
        return f"{project_short}_{hash_id}"

    def generate_test_case(self, diff_data: Dict, test_id: str):
        """Generate a complete test case with before/after files and metadata."""
        test_dir = self.output_dir / test_id
        test_dir.mkdir(exist_ok=True)

        # Save before version
        before_file = test_dir / "before.py"
        with open(before_file, 'w') as f:
            f.write(diff_data['before'])

        # Save after version
        after_file = test_dir / "after.py"
        with open(after_file, 'w') as f:
            f.write(diff_data['after'])

        # Save the diff
        diff_file = test_dir / "changes.diff"
        with open(diff_file, 'w') as f:
            f.write(diff_data['diff'])

        # Create metadata
        metadata = {
            'test_id': test_id,
            'project': diff_data['project'],
            'commit': diff_data['commit'],
            'file': diff_data['file'],
            'changed_functions': diff_data.get('changed_functions', [])
        }

        metadata_file = test_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Create a README for this test case
        readme_file = test_dir / "README.md"
        with open(readme_file, 'w') as f:
            f.write(f"# Test Case: {test_id}\n\n")
            f.write(f"**Project:** {diff_data['project']}\n\n")
            f.write(f"**Commit:** {diff_data['commit']}\n\n")
            f.write(f"**File:** {diff_data['file']}\n\n")

            if 'changed_functions' in diff_data:
                f.write("## Changed Functions\n\n")
                for func in diff_data['changed_functions']:
                    f.write(f"- `{func['name']}()`\n")
                f.write("\n")

            f.write("## Files\n\n")
            f.write("- `before.py` - Code before the change\n")
            f.write("- `after.py` - Code after the change\n")
            f.write("- `changes.diff` - Git diff showing the changes\n")
            f.write("- `metadata.json` - Test case metadata\n\n")

            f.write("## Usage\n\n")
            f.write("Run your type inference tool on both versions:\n\n")
            f.write("```bash\n")
            f.write("# Run on before version\n")
            f.write("python -m righttyper before.py > before_types.out\n\n")
            f.write("# Run on after version\n")
            f.write("python -m righttyper after.py > after_types.out\n\n")
            f.write("# Compare the results\n")
            f.write("diff before_types.out after_types.out\n")
            f.write("```\n")

        return test_dir

    def generate_all_test_cases(self, category: str = "function_changes_no_types"):
        """Generate test cases for all diffs in a category."""
        diffs = self.load_categorized_diffs(category)
        print(f"Generating test cases from '{category}' category...")
        print(f"Found {len(diffs)} candidates\n")

        test_cases = []
        for i, diff_data in enumerate(diffs, 1):
            test_id = self.create_test_id(diff_data)
            test_dir = self.generate_test_case(diff_data, test_id)
            test_cases.append({
                'id': test_id,
                'project': diff_data['project'],
                'file': diff_data['file'],
                'path': str(test_dir)
            })
            print(f"  [{i}/{len(diffs)}] Created: {test_id} ({diff_data['project']})")

        # Create an index file
        index_file = self.output_dir / "test_index.json"
        with open(index_file, 'w') as f:
            json.dump(test_cases, f, indent=2)

        # Create a master README
        readme_file = self.output_dir / "README.md"
        with open(readme_file, 'w') as f:
            f.write("# Differential Test Cases\n\n")
            f.write(f"This directory contains {len(test_cases)} test cases for differential testing.\n\n")
            f.write("## Test Cases\n\n")

            for tc in test_cases:
                f.write(f"### {tc['id']}\n")
                f.write(f"- **Project:** {tc['project']}\n")
                f.write(f"- **File:** {tc['file']}\n")
                f.write(f"- **Path:** `{tc['path']}`\n\n")

            f.write("## Batch Testing\n\n")
            f.write("You can run all test cases using the provided script:\n\n")
            f.write("```bash\n")
            f.write("python run_diff_tests.py\n")
            f.write("```\n")

        print(f"\nGenerated {len(test_cases)} test cases in: {self.output_dir}")
        print(f"Test index saved to: {index_file}")
        print(f"README saved to: {readme_file}")

        return test_cases

    def create_batch_test_script(self):
        """Create a script to run all test cases."""
        script_file = self.output_dir / "run_diff_tests.sh"
        with open(script_file, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Batch script to run type inference on all test cases\n\n")
            f.write("echo 'Running differential tests...'\n")
            f.write("echo ''\n\n")

            f.write("for test_dir in diff_test_cases/*/; do\n")
            f.write("    if [ -f \"$test_dir/before.py\" ]; then\n")
            f.write("        test_id=$(basename \"$test_dir\")\n")
            f.write("        echo \"Testing: $test_id\"\n\n")

            f.write("        # Run on before version\n")
            f.write("        python -m righttyper \"$test_dir/before.py\" > \"$test_dir/before_types.out\" 2>&1\n\n")

            f.write("        # Run on after version\n")
            f.write("        python -m righttyper \"$test_dir/after.py\" > \"$test_dir/after_types.out\" 2>&1\n\n")

            f.write("        # Compare results\n")
            f.write("        if diff -q \"$test_dir/before_types.out\" \"$test_dir/after_types.out\" > /dev/null; then\n")
            f.write("            echo \"  ✓ No difference in type inference\"\n")
            f.write("        else\n")
            f.write("            echo \"  ⚠ Type inference differs!\"\n")
            f.write("            diff \"$test_dir/before_types.out\" \"$test_dir/after_types.out\" > \"$test_dir/type_diff.txt\"\n")
            f.write("        fi\n")
            f.write("        echo ''\n")
            f.write("    fi\n")
            f.write("done\n\n")

            f.write("echo 'All tests completed!'\n")

        # Make executable
        script_file.chmod(0o755)
        print(f"\nBatch test script created: {script_file}")


def main():
    generator = TestCaseGenerator()

    # Generate test cases from the best candidates
    print("=" * 60)
    print("GENERATING DIFFERENTIAL TEST CASES")
    print("=" * 60)
    print()

    test_cases = generator.generate_all_test_cases("function_changes_no_types")

    # Also process function changes with types (for comparison)
    try:
        test_cases_with_types = generator.generate_all_test_cases("function_changes_with_types")
        print(f"\nAlso generated {len(test_cases_with_types)} test cases with type hints")
    except:
        pass

    # Create batch test script
    generator.create_batch_test_script()

    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("\n1. Review the test cases in: diff_test_cases/")
    print("2. Run batch tests with: ./diff_test_cases/run_diff_tests.sh")
    print("3. Check individual test results in each test case directory")


if __name__ == "__main__":
    main()
