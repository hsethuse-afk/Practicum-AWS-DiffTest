"""
Enhanced harness that uses environment builder for isolated test execution.
"""

from typing import Callable, Optional, Tuple
from ..contracts import TargetPair
from ..harness import HarnessBuilder
from .env_orchestrator import EnvironmentOrchestrator, EnvironmentSetup
from .docker_manager import DockerConfig


class EnhancedHarnessBuilder(HarnessBuilder):
    """
    Enhanced harness builder that supports Docker-based isolation.

    This extends the base HarnessBuilder to optionally run tests
    in isolated Docker containers with automatically discovered dependencies.
    """

    def __init__(self,
                 use_docker: bool = False,
                 docker_config: Optional[DockerConfig] = None,
                 base_requirements: Optional[list] = None):
        """
        Initialize enhanced harness builder.

        Args:
            use_docker: Whether to use Docker isolation
            docker_config: Docker configuration
            base_requirements: Base packages to always include
        """
        super().__init__()
        self.use_docker = use_docker
        self.env_orchestrator = EnvironmentOrchestrator(
            docker_config=docker_config,
            use_docker=use_docker
        )
        self.base_requirements = base_requirements or [
            'hypothesis',
            'coverage',
            'libcst',
            'righttyper',
        ]
        self.current_env: Optional[EnvironmentSetup] = None
        self.logger = None

    def build(self, target: TargetPair) -> Tuple[Callable, Callable]:
        """
        Build test harness with optional environment isolation.

        Args:
            target: TargetPair with file paths and function name

        Returns:
            Tuple of (function_a, function_b)
        """
        # Set up environment if using Docker
        if self.use_docker:
            if self.logger:
                self.logger.verbose("🔧 Setting up isolated environment...")

            self.current_env = self.env_orchestrator.setup_environment(
                file_a=target.file_a,
                file_b=target.file_b,
                base_requirements=self.base_requirements
            )

            if not self.current_env.success:
                error_msg = self.current_env.error_message or "Unknown error"
                raise RuntimeError(f"Failed to setup environment: {error_msg}")

            if self.logger and self.current_env.dependencies:
                report = self.env_orchestrator.get_dependency_report(
                    self.current_env.dependencies
                )
                self.logger.debug(f"\n{report}")

        # Use base harness builder to load functions
        # (In Docker mode, this would need to execute inside the container)
        return super().build(target)

    def cleanup(self) -> None:
        """Clean up environment resources."""
        if self.current_env and self.current_env.container_id:
            if self.logger:
                self.logger.verbose("🧹 Cleaning up environment...")
            self.env_orchestrator.cleanup(self.current_env.container_id)
            self.current_env = None

    def get_environment_info(self) -> Optional[EnvironmentSetup]:
        """
        Get information about the current environment.

        Returns:
            EnvironmentSetup if available, None otherwise
        """
        return self.current_env
