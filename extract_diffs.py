#!/usr/bin/env python3
"""
Extract git diffs from projects for differential testing.
This script clones repos, finds meaningful commits with test changes,
and extracts before/after versions for testing.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple


class DiffExtractor:
    def __init__(self, work_dir: str = "diff_test_data"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(exist_ok=True)

    def read_project_info(self, project_dir: Path) -> Dict:
        """Read project_info.txt and parse it."""
        info_file = project_dir / "project_info.txt"
        if not info_file.exists():
            return {}

        info = {}
        with open(info_file) as f:
            for line in f:
                if ':' in line:
                    key, value = line.strip().split(':', 1)
                    info[key.strip()] = value.strip()
        return info

    def clone_repo(self, url: str, target_dir: Path) -> bool:
        """Clone a git repository."""
        if target_dir.exists():
            print(f"Repository already exists at {target_dir}")
            return True

        try:
            subprocess.run(
                ['git', 'clone', '--depth=100', url, str(target_dir)],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to clone {url}: {e}")
            return False

    def get_commits_with_changes(self, repo_dir: Path, file_pattern: str = "*.py") -> List[str]:
        """Get commits that modified Python files."""
        try:
            result = subprocess.run(
                ['git', 'log', '--pretty=format:%H', '--', f'**/{file_pattern}'],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                check=True
            )
            commits = result.stdout.strip().split('\n')
            return [c for c in commits if c]
        except subprocess.CalledProcessError:
            return []

    def get_file_diff(self, repo_dir: Path, commit: str, filepath: str) -> Tuple[str, str, str]:
        """Get the diff for a specific file at a commit.
        Returns: (before_content, after_content, diff_text)
        """
        try:
            # Get the file content before the commit
            before = subprocess.run(
                ['git', 'show', f'{commit}^:{filepath}'],
                cwd=repo_dir,
                capture_output=True,
                text=True
            )

            # Get the file content after the commit
            after = subprocess.run(
                ['git', 'show', f'{commit}:{filepath}'],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                check=True
            )

            # Get the actual diff
            diff = subprocess.run(
                ['git', 'show', '--format=', commit, '--', filepath],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                check=True
            )

            return (before.stdout, after.stdout, diff.stdout)
        except subprocess.CalledProcessError:
            return ("", "", "")

    def extract_diffs_from_project(self, project_name: str, project_info: Dict,
                                   max_diffs: int = 5) -> List[Dict]:
        """Extract meaningful diffs from a project."""
        url = project_info.get('URL')
        if not url:
            print(f"No URL found for {project_name}")
            return []

        # Clone the repo
        repo_dir = self.work_dir / f"{project_name}_repo"
        if not self.clone_repo(url, repo_dir):
            return []

        # Get commits with Python file changes
        commits = self.get_commits_with_changes(repo_dir)
        print(f"Found {len(commits)} commits with Python changes in {project_name}")

        diffs = []
        for commit in commits[:max_diffs]:
            # Get changed files in this commit
            try:
                result = subprocess.run(
                    ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    check=True
                )
                changed_files = [f for f in result.stdout.strip().split('\n')
                               if f.endswith('.py')]

                for filepath in changed_files[:2]:  # Max 2 files per commit
                    before, after, diff_text = self.get_file_diff(repo_dir, commit, filepath)
                    if before and after and diff_text:
                        diffs.append({
                            'project': project_name,
                            'commit': commit,
                            'file': filepath,
                            'before': before,
                            'after': after,
                            'diff': diff_text
                        })
            except subprocess.CalledProcessError:
                continue

        return diffs

    def process_all_projects(self, extracted_dir: Path):
        """Process all projects in the extracted_tests directory."""
        all_diffs = []

        for project_dir in extracted_dir.iterdir():
            if not project_dir.is_dir():
                continue

            project_name = project_dir.name
            print(f"\n{'='*60}")
            print(f"Processing {project_name}")
            print(f"{'='*60}")

            project_info = self.read_project_info(project_dir)
            diffs = self.extract_diffs_from_project(project_name, project_info)
            all_diffs.extend(diffs)

            print(f"Extracted {len(diffs)} diffs from {project_name}")

        return all_diffs

    def save_diffs(self, diffs: List[Dict], output_file: str = "extracted_diffs.json"):
        """Save extracted diffs to a JSON file."""
        output_path = self.work_dir / output_file
        with open(output_path, 'w') as f:
            json.dump(diffs, f, indent=2)
        print(f"\nSaved {len(diffs)} diffs to {output_path}")

        # Also create individual diff files for easier inspection
        diffs_dir = self.work_dir / "individual_diffs"
        diffs_dir.mkdir(exist_ok=True)

        for i, diff_data in enumerate(diffs):
            diff_file = diffs_dir / f"{diff_data['project']}_{i:03d}.diff"
            with open(diff_file, 'w') as f:
                f.write(f"Project: {diff_data['project']}\n")
                f.write(f"Commit: {diff_data['commit']}\n")
                f.write(f"File: {diff_data['file']}\n")
                f.write(f"\n{'='*60}\n")
                f.write(diff_data['diff'])


def main():
    extractor = DiffExtractor()

    extracted_tests = Path("extracted_tests")
    if not extracted_tests.exists():
        print("extracted_tests directory not found!")
        return

    # Process all projects and extract diffs
    diffs = extractor.process_all_projects(extracted_tests)

    # Save the results
    extractor.save_diffs(diffs)

    print(f"\nTotal diffs extracted: {len(diffs)}")
    print(f"Results saved in: {extractor.work_dir}")


if __name__ == "__main__":
    main()
