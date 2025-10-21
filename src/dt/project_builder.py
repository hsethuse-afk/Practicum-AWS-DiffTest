"""
Project builder for differential testing from git diffs.

Handles:
- Cloning repositories
- Installing dependencies
- Setting up test environment
"""

import os
import shutil
import subprocess
import tempfile
from typing import Optional, Dict
from dataclasses import dataclass
from .logger import get_logger


@dataclass
class ProjectEnvironment:
    """Represents a built project environment"""
    project_root: str  # Root directory of cloned project
    repo_url: str     # Original repository URL
    commit: str       # Commit hash
    venv_path: Optional[str] = None  # Path to virtual environment (if created)
    cleanup: callable = None  # Cleanup function


class ProjectBuilder:
    """
    Build project environments for differential testing.

    Supports two modes:
    1. Local mode: Use existing local repository
    2. Clone mode: Clone repository from URL
    """

    def __init__(self):
        self.log = get_logger()

    def build_from_local(
        self,
        project_root: str,
        commit: str = "HEAD"
    ) -> ProjectEnvironment:
        """
        Use an existing local repository.

        Args:
            project_root: Path to local git repository
            commit: Commit to test (default: HEAD)

        Returns:
            ProjectEnvironment pointing to local repository
        """
        if not os.path.exists(os.path.join(project_root, ".git")):
            raise ValueError(f"{project_root} is not a git repository")

        # Verify commit exists
        try:
            result = subprocess.run(
                ["git", "rev-parse", commit],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True
            )
            commit_hash = result.stdout.strip()
        except subprocess.CalledProcessError:
            raise ValueError(f"Commit {commit} not found in {project_root}")

        self.log.verbose(
            f"[ProjectBuilder] Using local repository: {project_root} @ {commit_hash}"
        )

        return ProjectEnvironment(
            project_root=project_root,
            repo_url="local",
            commit=commit_hash,
            cleanup=lambda: None  # No cleanup for local repos
        )

    def build_from_url(
        self,
        repo_url: str,
        commit: str = "HEAD",
        install_deps: bool = True
    ) -> ProjectEnvironment:
        """
        Clone a repository and set up the environment.

        Args:
            repo_url: Git repository URL
            commit: Commit to checkout
            install_deps: Whether to install dependencies

        Returns:
            ProjectEnvironment with cloned repository
        """
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="difftest_project_")

        try:
            # Clone repository
            self.log.verbose(f"[ProjectBuilder] Cloning {repo_url} to {temp_dir}")
            subprocess.run(
                ["git", "clone", repo_url, temp_dir],
                capture_output=True,
                text=True,
                check=True
            )

            # Checkout specific commit
            self.log.verbose(f"[ProjectBuilder] Checking out {commit}")
            subprocess.run(
                ["git", "checkout", commit],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                check=True
            )

            # Get actual commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                check=True
            )
            commit_hash = result.stdout.strip()

            # Install dependencies if requested
            venv_path = None
            if install_deps:
                venv_path = self._install_dependencies(temp_dir)

            # Cleanup function
            def cleanup():
                try:
                    shutil.rmtree(temp_dir)
                    self.log.debug(
                        f"[ProjectBuilder] Cleaned up project directory: {temp_dir}"
                    )
                except Exception as e:
                    self.log.debug(
                        f"[ProjectBuilder] Failed to cleanup: {e}"
                    )

            return ProjectEnvironment(
                project_root=temp_dir,
                repo_url=repo_url,
                commit=commit_hash,
                venv_path=venv_path,
                cleanup=cleanup
            )

        except Exception as e:
            # Cleanup on error
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"Failed to build project from {repo_url}: {e}")

    def _create_venv(self, project_root: str) -> str:
        """
        Create a virtual environment for the project.

        Args:
            project_root: Root directory of the project

        Returns:
            Path to virtual environment
        """
        venv_path = os.path.join(project_root, ".venv")

        self.log.verbose(f"[ProjectBuilder] Creating virtual environment at {venv_path}")

        try:
            subprocess.run(
                ["python3", "-m", "venv", venv_path],
                capture_output=True,
                text=True,
                check=True
            )
            self.log.verbose("[ProjectBuilder] Virtual environment created successfully")
            return venv_path
        except subprocess.CalledProcessError as e:
            self.log.debug(f"[ProjectBuilder] Failed to create venv: {e.stderr}")
            return None

    def _get_venv_python(self, venv_path: str) -> str:
        """Get path to Python executable in virtual environment"""
        if os.name == 'nt':  # Windows
            return os.path.join(venv_path, "Scripts", "python.exe")
        else:  # Unix/Linux/Mac
            return os.path.join(venv_path, "bin", "python")

    def _get_venv_pip(self, venv_path: str) -> str:
        """Get path to pip executable in virtual environment"""
        if os.name == 'nt':  # Windows
            return os.path.join(venv_path, "Scripts", "pip.exe")
        else:  # Unix/Linux/Mac
            return os.path.join(venv_path, "bin", "pip")

    def _install_dependencies(self, project_root: str, use_venv: bool = True) -> Optional[str]:
        """
        Install project dependencies.

        Strategy:
        1. Create virtual environment (if use_venv=True)
        2. Look for requirements.txt
        3. Look for pyproject.toml
        4. Install dependencies

        Args:
            project_root: Root directory of the project
            use_venv: Whether to create and use virtual environment

        Returns:
            Path to virtual environment (None if not using venv)
        """
        venv_path = None
        pip_cmd = "pip"

        # Create virtual environment if requested
        if use_venv:
            venv_path = self._create_venv(project_root)
            if venv_path:
                pip_cmd = self._get_venv_pip(venv_path)
                self.log.verbose(f"[ProjectBuilder] Using pip from venv: {pip_cmd}")

        requirements_file = os.path.join(project_root, "requirements.txt")
        pyproject_file = os.path.join(project_root, "pyproject.toml")

        # Try requirements.txt first
        if os.path.exists(requirements_file):
            self.log.verbose(
                f"[ProjectBuilder] Installing dependencies from requirements.txt"
            )

            try:
                subprocess.run(
                    [pip_cmd, "install", "-q", "-r", requirements_file],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    check=True
                )
                self.log.verbose("[ProjectBuilder] Dependencies installed successfully")
            except subprocess.CalledProcessError as e:
                self.log.debug(
                    f"[ProjectBuilder] Failed to install dependencies: {e.stderr}"
                )

            return venv_path

        # Try pyproject.toml
        if os.path.exists(pyproject_file):
            self.log.verbose(
                f"[ProjectBuilder] Installing project from pyproject.toml"
            )

            try:
                # Install the project in editable mode to get dependencies
                subprocess.run(
                    [pip_cmd, "install", "-q", "-e", "."],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    check=True
                )
                self.log.verbose("[ProjectBuilder] Project and dependencies installed successfully")
            except subprocess.CalledProcessError as e:
                self.log.debug(
                    f"[ProjectBuilder] Failed to install project: {e.stderr}"
                )

            return venv_path

        # No dependency file found
        self.log.verbose(
            "[ProjectBuilder] No requirements.txt or pyproject.toml found, skipping dependency install"
        )
        return venv_path

    def build_from_diff_with_repo(
        self,
        diff_content: str,
        repo_url: str,
        commit: Optional[str] = None
    ) -> ProjectEnvironment:
        """
        Build environment from a diff and repository URL.

        Args:
            diff_content: Git diff content
            repo_url: Repository URL to clone
            commit: Optional specific commit (extracted from diff if not provided)

        Returns:
            ProjectEnvironment ready for testing
        """
        # Extract commit from diff if not provided
        if commit is None:
            commit = self._extract_commit_from_diff(diff_content)
            if commit is None:
                commit = "HEAD"

        # Build from URL
        return self.build_from_url(repo_url, commit)

    def _extract_commit_from_diff(self, diff_content: str) -> Optional[str]:
        """
        Try to extract commit hash from diff header.

        Args:
            diff_content: Raw git diff output

        Returns:
            Commit hash if found, None otherwise
        """
        import re

        # Look for patterns like:
        # commit abc123...
        # From abc123...
        match = re.search(r'^(?:commit|From)\s+([a-f0-9]{40})', diff_content, re.MULTILINE)
        if match:
            return match.group(1)

        return None
