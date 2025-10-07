"""
Docker manager for creating and managing isolated test environments.
"""

import subprocess
import os
import tempfile
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class DockerConfig:
    """Configuration for Docker environment."""

    image_name: str = "difftest-env"
    container_name: str = "difftest-runner"
    python_version: str = "3.11"
    work_dir: str = "/app"
    volumes: Dict[str, str] = None  # host_path: container_path
    environment: Dict[str, str] = None


class DockerManager:
    """
    Manages Docker containers for isolated test execution.

    This manager handles:
    - Building Docker images with dependencies
    - Creating and managing containers
    - Executing tests inside containers
    - Cleaning up resources
    """

    def __init__(self, config: Optional[DockerConfig] = None):
        self.config = config or DockerConfig()
        self.logger = None

    def check_docker_available(self) -> bool:
        """
        Check if Docker is available on the system.

        Returns:
            True if Docker is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def build_image(self, dockerfile_path: str, requirements: List[str]) -> bool:
        """
        Build a Docker image with the specified requirements.

        Args:
            dockerfile_path: Path to the Dockerfile
            requirements: List of Python packages to install

        Returns:
            True if build succeeded, False otherwise
        """
        if not self.check_docker_available():
            if self.logger:
                self.logger.error("Docker is not available on this system")
            return False

        try:
            # Create a temporary requirements file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                delete=False,
                dir=os.path.dirname(dockerfile_path)
            ) as tmp_req:
                tmp_req.write("# Dynamic requirements for differential testing\n")
                for pkg in requirements:
                    tmp_req.write(f"{pkg}\n")
                tmp_req_path = tmp_req.name

            # Build the Docker image
            build_context = os.path.dirname(dockerfile_path)
            cmd = [
                "docker", "build",
                "-t", self.config.image_name,
                "-f", dockerfile_path,
                build_context
            ]

            if self.logger:
                self.logger.verbose(f"Building Docker image: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            # Clean up temporary file
            try:
                os.unlink(tmp_req_path)
            except:
                pass

            if result.returncode == 0:
                if self.logger:
                    self.logger.verbose(f"✓ Docker image '{self.config.image_name}' built successfully")
                return True
            else:
                if self.logger:
                    self.logger.error(f"Docker build failed: {result.stderr}")
                return False

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error building Docker image: {e}")
            return False

    def create_container(self,
                        mount_paths: Optional[Dict[str, str]] = None,
                        env_vars: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Create a Docker container.

        Args:
            mount_paths: Dictionary of host_path: container_path to mount
            env_vars: Environment variables to set in the container

        Returns:
            Container ID if successful, None otherwise
        """
        try:
            cmd = [
                "docker", "create",
                "--name", self.config.container_name,
            ]

            # Add volume mounts
            volumes = mount_paths or self.config.volumes or {}
            for host_path, container_path in volumes.items():
                cmd.extend(["-v", f"{host_path}:{container_path}"])

            # Add environment variables
            env = env_vars or self.config.environment or {}
            for key, value in env.items():
                cmd.extend(["-e", f"{key}={value}"])

            # Add working directory
            cmd.extend(["-w", self.config.work_dir])

            # Add image name
            cmd.append(self.config.image_name)

            if self.logger:
                self.logger.debug(f"Creating container: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                container_id = result.stdout.strip()
                if self.logger:
                    self.logger.verbose(f"✓ Container created: {container_id[:12]}")
                return container_id
            else:
                if self.logger:
                    self.logger.error(f"Failed to create container: {result.stderr}")
                return None

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating container: {e}")
            return None

    def start_container(self, container_id: str) -> bool:
        """
        Start a Docker container.

        Args:
            container_id: Container ID or name

        Returns:
            True if started successfully, False otherwise
        """
        try:
            result = subprocess.run(
                ["docker", "start", container_id],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error starting container: {e}")
            return False

    def execute_in_container(self,
                            container_id: str,
                            command: List[str],
                            workdir: Optional[str] = None) -> tuple[int, str, str]:
        """
        Execute a command inside a running container.

        Args:
            container_id: Container ID or name
            command: Command to execute as list of strings
            workdir: Working directory for the command

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            cmd = ["docker", "exec"]

            if workdir:
                cmd.extend(["-w", workdir])

            cmd.append(container_id)
            cmd.extend(command)

            if self.logger:
                self.logger.debug(f"Executing in container: {' '.join(command)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            return result.returncode, result.stdout, result.stderr

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error executing in container: {e}")
            return -1, "", str(e)

    def install_requirements(self,
                            container_id: str,
                            requirements: List[str]) -> bool:
        """
        Install Python requirements inside a container.

        Args:
            container_id: Container ID or name
            requirements: List of package names to install

        Returns:
            True if installation succeeded, False otherwise
        """
        if not requirements:
            return True

        # Create pip install command
        pip_cmd = ["pip", "install", "--no-cache-dir"] + requirements

        returncode, stdout, stderr = self.execute_in_container(
            container_id,
            pip_cmd
        )

        if returncode == 0:
            if self.logger:
                self.logger.verbose(f"✓ Installed {len(requirements)} packages")
            return True
        else:
            if self.logger:
                self.logger.error(f"Failed to install packages: {stderr}")
            return False

    def copy_to_container(self,
                         container_id: str,
                         src_path: str,
                         dst_path: str) -> bool:
        """
        Copy files to a container.

        Args:
            container_id: Container ID or name
            src_path: Source path on host
            dst_path: Destination path in container

        Returns:
            True if copy succeeded, False otherwise
        """
        try:
            cmd = ["docker", "cp", src_path, f"{container_id}:{dst_path}"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            return result.returncode == 0

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error copying to container: {e}")
            return False

    def stop_container(self, container_id: str) -> bool:
        """
        Stop a running container.

        Args:
            container_id: Container ID or name

        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            result = subprocess.run(
                ["docker", "stop", container_id],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error stopping container: {e}")
            return False

    def remove_container(self, container_id: str, force: bool = False) -> bool:
        """
        Remove a container.

        Args:
            container_id: Container ID or name
            force: Force removal even if running

        Returns:
            True if removed successfully, False otherwise
        """
        try:
            cmd = ["docker", "rm"]
            if force:
                cmd.append("-f")
            cmd.append(container_id)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error removing container: {e}")
            return False

    def cleanup(self, container_id: Optional[str] = None) -> None:
        """
        Clean up Docker resources.

        Args:
            container_id: Specific container to clean up, or None for default
        """
        cid = container_id or self.config.container_name

        # Try to stop and remove the container
        self.stop_container(cid)
        self.remove_container(cid, force=True)

        if self.logger:
            self.logger.debug(f"Cleaned up container: {cid}")
