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
        # Create temporary directory in project root
        project_base = os.path.join(os.path.dirname(__file__), "..", "..")
        project_base = os.path.abspath(project_base)
        temp_parent = os.path.join(project_base, ".difftest_temp")
        os.makedirs(temp_parent, exist_ok=True)
        temp_dir = tempfile.mkdtemp(prefix="difftest_project_", dir=temp_parent)

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

            # Cleanup function (disabled to keep temp directories for inspection)
            def cleanup():
                self.log.debug(
                    f"[ProjectBuilder] Keeping project directory for inspection: {temp_dir}"
                )
                # Uncomment below to enable auto-cleanup:
                # try:
                #     shutil.rmtree(temp_dir)
                #     self.log.debug(
                #         f"[ProjectBuilder] Cleaned up project directory: {temp_dir}"
                #     )
                # except Exception as e:
                #     self.log.debug(
                #         f"[ProjectBuilder] Failed to cleanup: {e}"
                #     )

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

        # Try pyproject.toml or setup.py
        setup_py_file = os.path.join(project_root, "setup.py")

        if os.path.exists(pyproject_file) or os.path.exists(setup_py_file):
            self.log.verbose(
                f"[ProjectBuilder] Installing project in editable mode"
            )

            try:
                # First, install build dependencies
                # For older projects, we need an older setuptools version that has dep_util
                self.log.verbose("[ProjectBuilder] Installing build dependencies")
                subprocess.run(
                    [pip_cmd, "install", "--upgrade", "pip", "wheel"],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                # Install setuptools<58 for compatibility with older projects
                # setuptools 58+ removed setuptools.dep_util
                subprocess.run(
                    [pip_cmd, "install", "setuptools<58", "setuptools-scm[toml]"],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                # For older scientific projects, install common dependencies
                subprocess.run(
                    [pip_cmd, "install", "extension-helpers", "numpy<2.0", "cython"],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    timeout=180
                )

                # Install the project in editable mode to get dependencies
                # Use --no-build-isolation so it uses our setuptools<58
                self.log.verbose("[ProjectBuilder] Running pip install -e . --no-build-isolation")
                result = subprocess.run(
                    [pip_cmd, "install", "-e", ".", "--no-build-isolation"],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout for complex builds with compilation
                )

                if result.returncode == 0:
                    self.log.verbose("[ProjectBuilder] Project and dependencies installed successfully")
                else:
                    self.log.normal(f"⚠️  Warning: pip install -e . failed (exit code: {result.returncode})")
                    if result.stderr:
                        # Show last 15 lines of stderr for debugging
                        stderr_lines = result.stderr.strip().split('\n')
                        self.log.normal("   Last few error lines:")
                        for line in stderr_lines[-15:]:
                            if line.strip():
                                self.log.normal(f"   {line}")

                    # Try build_ext --inplace as fallback for projects with C extensions
                    if os.path.exists(setup_py_file):
                        self.log.normal("   Attempting fallback: python setup.py build_ext --inplace")
                        try:
                            python_cmd = self._get_venv_python(venv_path) if venv_path else "python3"
                            fallback_result = subprocess.run(
                                [python_cmd, "setup.py", "build_ext", "--inplace"],
                                cwd=project_root,
                                capture_output=True,
                                text=True,
                                timeout=600  # 10 minute timeout for complex builds
                            )
                            if fallback_result.returncode == 0:
                                self.log.normal("   ✓ Fallback build succeeded - C extensions compiled")
                            else:
                                self.log.normal(f"   ✗ Fallback build also failed")
                                if fallback_result.stderr:
                                    stderr_lines = fallback_result.stderr.strip().split('\n')
                                    for line in stderr_lines[-10:]:
                                        if line.strip():
                                            self.log.debug(f"   {line}")
                        except subprocess.TimeoutExpired:
                            self.log.normal("   ✗ Fallback build timed out after 10 minutes")
                        except Exception as e:
                            self.log.debug(f"   Fallback build error: {e}")

            except subprocess.TimeoutExpired:
                self.log.normal(f"⚠️  Warning: Installation timed out after 5 minutes")
            except subprocess.CalledProcessError as e:
                self.log.normal(f"⚠️  Warning: Failed to install project")
                self.log.debug(f"[ProjectBuilder] Failed to install project: {e.stderr}")

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
