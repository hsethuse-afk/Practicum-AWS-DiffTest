"""
Environment orchestrator that coordinates dependency scanning and Docker setup.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass

from .dependency_scanner import DependencyScanner, DependencyInfo
from .docker_manager import DockerManager, DockerConfig


@dataclass
class EnvironmentSetup:
    """Result of environment setup."""

    success: bool
    container_id: Optional[str] = None
    dependencies: Optional[DependencyInfo] = None
    requirements: Optional[List[str]] = None
    error_message: Optional[str] = None


class EnvironmentOrchestrator:
    """
    Orchestrates the complete environment setup process.

    This orchestrator:
    1. Scans code for dependencies
    2. Builds Docker image with dependencies
    3. Creates isolated container
    4. Installs all required packages
    5. Prepares environment for test execution
    """

    def __init__(self,
                 docker_config: Optional[DockerConfig] = None,
                 use_docker: bool = True):
        """
        Initialize the environment orchestrator.

        Args:
            docker_config: Docker configuration
            use_docker: Whether to use Docker (False for local testing)
        """
        self.scanner = DependencyScanner()
        self.docker_manager = DockerManager(docker_config) if use_docker else None
        self.use_docker = use_docker
        self.logger = None

    def setup_environment(self,
                         file_a: str,
                         file_b: str,
                         project_root: Optional[str] = None,
                         base_requirements: Optional[List[str]] = None) -> EnvironmentSetup:
        """
        Set up complete testing environment for files A and B.

        Args:
            file_a: Path to version A file
            file_b: Path to version B file
            project_root: Root directory of the project (optional)
            base_requirements: Base requirements to always include

        Returns:
            EnvironmentSetup with results
        """
        try:
            # Step 1: Scan dependencies
            if self.logger:
                self.logger.verbose("🔍 Scanning dependencies...")

            deps = self._scan_dependencies(file_a, file_b, project_root)

            # Step 2: Collect all requirements
            requirements = self._collect_requirements(deps, base_requirements)

            if self.logger:
                self.logger.verbose(f"📦 Found {len(requirements)} packages to install")
                self.logger.debug(f"Packages: {', '.join(requirements)}")

            # Step 3: Setup environment (Docker or local)
            if self.use_docker:
                container_id = self._setup_docker_environment(
                    requirements,
                    file_a,
                    file_b
                )
                if not container_id:
                    return EnvironmentSetup(
                        success=False,
                        error_message="Failed to set up Docker environment"
                    )
            else:
                container_id = None
                self._setup_local_environment(requirements)

            if self.logger:
                self.logger.verbose("✅ Environment setup complete")

            return EnvironmentSetup(
                success=True,
                container_id=container_id,
                dependencies=deps,
                requirements=requirements
            )

        except Exception as e:
            if self.logger:
                self.logger.error(f"Environment setup failed: {e}")

            return EnvironmentSetup(
                success=False,
                error_message=str(e)
            )

    def _scan_dependencies(self,
                          file_a: str,
                          file_b: str,
                          project_root: Optional[str]) -> DependencyInfo:
        """
        Scan all dependencies for the test files.

        Args:
            file_a: Path to version A file
            file_b: Path to version B file
            project_root: Optional project root directory

        Returns:
            DependencyInfo object
        """
        deps = DependencyInfo()

        # Scan file A
        if os.path.exists(file_a):
            deps_a = self.scanner.scan_file(file_a)
            deps.merge(deps_a)
            if self.logger:
                self.logger.debug(f"Scanned {file_a}: {len(deps_a.imports)} imports")

        # Scan file B
        if os.path.exists(file_b):
            deps_b = self.scanner.scan_file(file_b)
            deps.merge(deps_b)
            if self.logger:
                self.logger.debug(f"Scanned {file_b}: {len(deps_b.imports)} imports")

        # Scan project root if provided
        if project_root and os.path.exists(project_root):
            # Get directory containing files
            dir_a = os.path.dirname(os.path.abspath(file_a))
            if dir_a:
                dir_deps = self.scanner.scan_directory(dir_a, recursive=False)
                deps.merge(dir_deps)

        return deps

    def _collect_requirements(self,
                             deps: DependencyInfo,
                             base_requirements: Optional[List[str]] = None) -> List[str]:
        """
        Collect all requirements to install.

        Args:
            deps: DependencyInfo object
            base_requirements: Base requirements to include

        Returns:
            List of package names
        """
        requirements = set()

        # Add base requirements (framework dependencies)
        if base_requirements:
            requirements.update(base_requirements)

        # Add discovered requirements
        discovered = self.scanner.get_install_requirements(deps)
        requirements.update(discovered)

        return sorted(list(requirements))

    def _setup_docker_environment(self,
                                 requirements: List[str],
                                 file_a: str,
                                 file_b: str) -> Optional[str]:
        """
        Set up Docker environment.

        Args:
            requirements: List of packages to install
            file_a: Path to version A file
            file_b: Path to version B file

        Returns:
            Container ID if successful, None otherwise
        """
        if not self.docker_manager:
            return None

        # Check Docker availability
        if not self.docker_manager.check_docker_available():
            if self.logger:
                self.logger.error("Docker is not available")
            return None

        # Build image
        dockerfile = self._find_dockerfile()
        if not dockerfile:
            if self.logger:
                self.logger.error("Dockerfile not found")
            return None

        if self.logger:
            self.logger.verbose("🐳 Building Docker image...")

        if not self.docker_manager.build_image(dockerfile, requirements):
            return None

        # Create container
        if self.logger:
            self.logger.verbose("📦 Creating container...")

        # Prepare volume mounts
        volumes = self._prepare_volumes(file_a, file_b)

        container_id = self.docker_manager.create_container(
            mount_paths=volumes,
            env_vars={"PYTHONUNBUFFERED": "1"}
        )

        if not container_id:
            return None

        # Start container
        if not self.docker_manager.start_container(container_id):
            if self.logger:
                self.logger.error("Failed to start container")
            return None

        # Install requirements inside container
        if requirements:
            if self.logger:
                self.logger.verbose("📥 Installing requirements in container...")

            if not self.docker_manager.install_requirements(container_id, requirements):
                if self.logger:
                    self.logger.warning("Some packages failed to install")

        return container_id

    def _setup_local_environment(self, requirements: List[str]) -> None:
        """
        Set up local environment (install packages locally).

        Args:
            requirements: List of packages to install
        """
        if not requirements:
            return

        import subprocess

        if self.logger:
            self.logger.verbose(f"📥 Installing {len(requirements)} packages locally...")

        try:
            cmd = ["pip", "install", "--quiet"] + requirements
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                if self.logger:
                    self.logger.verbose("✅ Packages installed successfully")
            else:
                if self.logger:
                    self.logger.warning(f"Some packages failed: {result.stderr}")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to install packages: {e}")

    def _find_dockerfile(self) -> Optional[str]:
        """
        Find the Dockerfile in the project.

        Returns:
            Path to Dockerfile, or None if not found
        """
        # Look for Dockerfile in current directory and parent directories
        current = Path.cwd()

        for _ in range(3):  # Check up to 3 levels up
            dockerfile = current / "Dockerfile"
            if dockerfile.exists():
                return str(dockerfile)
            current = current.parent

        return None

    def _prepare_volumes(self,
                        file_a: str,
                        file_b: str) -> Dict[str, str]:
        """
        Prepare volume mounts for Docker container.

        Args:
            file_a: Path to version A file
            file_b: Path to version B file

        Returns:
            Dictionary of host_path: container_path
        """
        volumes = {}

        # Mount directory containing the files
        dir_a = os.path.dirname(os.path.abspath(file_a))
        dir_b = os.path.dirname(os.path.abspath(file_b))

        # Mount both directories if they're different
        if dir_a:
            volumes[dir_a] = "/app/code_a"

        if dir_b and dir_b != dir_a:
            volumes[dir_b] = "/app/code_b"
        elif not dir_b:
            volumes[dir_a] = "/app/code_b"

        return volumes

    def cleanup(self, container_id: Optional[str] = None) -> None:
        """
        Clean up environment resources.

        Args:
            container_id: Container to clean up (if using Docker)
        """
        if self.docker_manager and container_id:
            if self.logger:
                self.logger.debug("🧹 Cleaning up Docker resources...")
            self.docker_manager.cleanup(container_id)

    def get_dependency_report(self, deps: DependencyInfo) -> str:
        """
        Generate a human-readable dependency report.

        Args:
            deps: DependencyInfo object

        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("DEPENDENCY REPORT")
        report.append("=" * 60)

        report.append(f"\nStandard Library Modules ({len(deps.stdlib_modules)}):")
        for mod in sorted(deps.stdlib_modules):
            report.append(f"  - {mod}")

        report.append(f"\nThird-Party Packages ({len(deps.third_party_packages)}):")
        for pkg in sorted(deps.third_party_packages):
            report.append(f"  - {pkg}")

        report.append(f"\nLocal Imports ({len(deps.local_imports)}):")
        for imp in sorted(deps.local_imports):
            report.append(f"  - {imp}")

        if deps.requirements_files:
            report.append(f"\nRequirements Files ({len(deps.requirements_files)}):")
            for req_file in deps.requirements_files:
                report.append(f"  - {req_file}")

        report.append("=" * 60)

        return "\n".join(report)
