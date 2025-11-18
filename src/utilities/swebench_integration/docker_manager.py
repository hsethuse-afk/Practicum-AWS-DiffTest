"""
Manage SWE-bench Docker containers for isolated testing.

This module provides a high-level interface to interact with SWE-bench's
Docker infrastructure, including container lifecycle management and file operations.
"""

import os
import io
import tarfile
import tempfile
from typing import Optional, Dict, List
from pathlib import Path


class DockerManager:
    """
    Wrapper around SWE-bench Docker infrastructure.

    Manages Docker containers for running differential tests in isolated
    environments with correct dependencies and repository states.
    """

    def __init__(self):
        """Initialize Docker manager with client connection."""
        try:
            import docker
            self.client = docker.from_env()
            self.docker_available = True
        except ImportError:
            print("Warning: docker package not installed. Install with: pip install docker")
            self.docker_available = False
            self.client = None
        except Exception as e:
            print(f"Warning: Could not connect to Docker daemon: {e}")
            self.docker_available = False
            self.client = None

    def is_available(self) -> bool:
        """Check if Docker is available and running."""
        return self.docker_available and self.client is not None

    def start_instance_container(
        self,
        instance: Dict,
        image_key: Optional[str] = None,
        namespace: str = 'difftesting'
    ):
        """
        Start a Docker container for a SWE-bench instance.

        Args:
            instance: SWE-bench instance dictionary
            image_key: Docker image name (if None, will be constructed from instance)
            namespace: Docker image namespace

        Returns:
            Docker container object

        Raises:
            RuntimeError: If Docker is not available or image doesn't exist

        Example:
            >>> manager = DockerManager()
            >>> container = manager.start_instance_container(instance)
        """
        if not self.is_available():
            raise RuntimeError("Docker is not available")

        # Construct image key if not provided
        if image_key is None:
            instance_id = instance['instance_id']
            image_key = f"{namespace}.{instance_id}:latest"

        try:
            # Start container in detached mode
            container = self.client.containers.run(
                image=image_key,
                command="/bin/bash",
                detach=True,
                tty=True,
                stdin_open=True,
                working_dir="/testbed",
                remove=False,  # Don't auto-remove so we can extract files
            )

            print(f"Started container {container.short_id} for {instance.get('instance_id', 'unknown')}")
            return container

        except Exception as e:
            raise RuntimeError(f"Failed to start container: {e}")

    def extract_file(self, container, file_path: str) -> str:
        """
        Extract file content from container.

        Args:
            container: Docker container object
            file_path: Path to file inside container (absolute or relative to /testbed)

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If file doesn't exist in container
            RuntimeError: If extraction fails

        Example:
            >>> content = manager.extract_file(container, '/testbed/src/module.py')
        """
        # Ensure absolute path
        if not file_path.startswith('/'):
            file_path = f"/testbed/{file_path}"

        try:
            # Execute cat command to read file
            result = container.exec_run(f"cat {file_path}")

            if result.exit_code != 0:
                raise FileNotFoundError(f"File not found: {file_path}")

            return result.output.decode('utf-8')

        except Exception as e:
            raise RuntimeError(f"Failed to extract file {file_path}: {e}")

    def save_file_locally(
        self,
        container,
        container_path: str,
        local_path: str
    ) -> None:
        """
        Extract file from container and save to local filesystem.

        Args:
            container: Docker container object
            container_path: Path to file inside container
            local_path: Local path where file should be saved

        Example:
            >>> manager.save_file_locally(container, '/testbed/foo.py', 'temp/foo.py')
        """
        # Extract content
        content = self.extract_file(container, container_path)

        # Ensure parent directory exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Write to local file
        with open(local_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Saved {container_path} to {local_path}")

    def write_to_container(
        self,
        container,
        content: str,
        container_path: str
    ) -> None:
        """
        Write content to a file inside the container.

        Args:
            container: Docker container object
            content: Content to write
            container_path: Path where to write inside container

        Raises:
            RuntimeError: If write operation fails

        Example:
            >>> manager.write_to_container(container, patch_content, '/testbed/fix.patch')
        """
        try:
            # Use heredoc to write content
            # Escape any single quotes in content
            escaped_content = content.replace("'", "'\"'\"'")

            cmd = f"cat > {container_path} << 'DIFFTESTING_EOF'\n{content}\nDIFFTESTING_EOF"

            result = container.exec_run(["/bin/bash", "-c", cmd])

            if result.exit_code != 0:
                raise RuntimeError(f"Write failed: {result.output.decode('utf-8')}")

            print(f"Wrote content to {container_path}")

        except Exception as e:
            raise RuntimeError(f"Failed to write to container: {e}")

    def apply_patch(
        self,
        container,
        patch_content: str,
        patch_file: str = '/testbed/temp.patch'
    ) -> bool:
        """
        Apply a git patch inside the container.

        Tries multiple patch application methods in order of preference:
        1. git apply -v
        2. patch -p1
        3. git apply --3way

        Args:
            container: Docker container object
            patch_content: Content of the patch (unified diff format)
            patch_file: Where to write the patch inside container

        Returns:
            True if patch applied successfully, False otherwise

        Example:
            >>> success = manager.apply_patch(container, instance['patch'])
        """
        # Write patch to container
        self.write_to_container(container, patch_content, patch_file)

        # Try multiple patch application methods
        methods = [
            f"git apply -v {patch_file}",
            f"patch -p1 < {patch_file}",
            f"git apply --3way {patch_file}",
        ]

        for i, method in enumerate(methods, 1):
            print(f"Attempting patch method {i}/{len(methods)}: {method}")

            result = container.exec_run(
                ["/bin/bash", "-c", method],
                workdir="/testbed"
            )

            if result.exit_code == 0:
                print(f"✓ Patch applied successfully using: {method}")
                return True
            else:
                error_msg = result.output.decode('utf-8')
                print(f"✗ Method failed: {error_msg[:200]}")

        print("✗ All patch methods failed")
        return False

    def exec_command(
        self,
        container,
        command: str,
        workdir: str = '/testbed'
    ) -> tuple:
        """
        Execute a command inside the container.

        Args:
            container: Docker container object
            command: Command to execute
            workdir: Working directory for command execution

        Returns:
            Tuple of (exit_code, output)

        Example:
            >>> exit_code, output = manager.exec_command(container, 'pytest tests/')
        """
        result = container.exec_run(
            ["/bin/bash", "-c", command],
            workdir=workdir
        )

        return result.exit_code, result.output.decode('utf-8')

    def stop_container(self, container, remove: bool = True) -> None:
        """
        Stop and optionally remove a container.

        Args:
            container: Docker container object
            remove: If True, remove container after stopping

        Example:
            >>> manager.stop_container(container, remove=True)
        """
        try:
            print(f"Stopping container {container.short_id}...")
            container.stop(timeout=10)

            if remove:
                print(f"Removing container {container.short_id}...")
                container.remove()

            print("Container cleaned up successfully")

        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")

    def extract_modified_files(
        self,
        container,
        patch: str,
        output_dir: str,
        state: str = 'before'
    ) -> List[str]:
        """
        Extract all files modified by a patch from the container.

        Args:
            container: Docker container object
            patch: Unified diff patch content
            output_dir: Local directory to save extracted files
            state: 'before' or 'after' (for naming subdirectories)

        Returns:
            List of local file paths that were extracted

        Example:
            >>> files = manager.extract_modified_files(container, patch, 'temp/', 'before')
            >>> print(files)
            ['temp/before/src/module.py', 'temp/before/tests/test.py']
        """
        from .patch_parser import PatchParser

        # Parse patch to get modified files
        modified_files = PatchParser.extract_python_files(patch)

        if not modified_files:
            print("Warning: No Python files found in patch")
            return []

        local_files = []

        for file_path in modified_files:
            # Construct paths
            container_path = f"/testbed/{file_path}"
            local_path = os.path.join(output_dir, state, file_path)

            try:
                # Extract and save file
                self.save_file_locally(container, container_path, local_path)
                local_files.append(local_path)

            except Exception as e:
                print(f"Warning: Could not extract {file_path}: {e}")

        return local_files

    def get_container_info(self, container) -> Dict:
        """
        Get information about a running container.

        Args:
            container: Docker container object

        Returns:
            Dictionary with container information

        Example:
            >>> info = manager.get_container_info(container)
            >>> print(info['status'])
            'running'
        """
        container.reload()  # Refresh container state

        return {
            'id': container.id,
            'short_id': container.short_id,
            'name': container.name,
            'status': container.status,
            'image': container.image.tags[0] if container.image.tags else 'unknown',
        }

    def check_file_exists(self, container, file_path: str) -> bool:
        """
        Check if a file exists inside the container.

        Args:
            container: Docker container object
            file_path: Path to check (absolute or relative to /testbed)

        Returns:
            True if file exists, False otherwise

        Example:
            >>> exists = manager.check_file_exists(container, '/testbed/src/foo.py')
        """
        if not file_path.startswith('/'):
            file_path = f"/testbed/{file_path}"

        result = container.exec_run(f"test -f {file_path}")
        return result.exit_code == 0

    def list_directory(self, container, directory: str = '/testbed') -> List[str]:
        """
        List contents of a directory inside the container.

        Args:
            container: Docker container object
            directory: Directory to list

        Returns:
            List of file/directory names

        Example:
            >>> files = manager.list_directory(container, '/testbed/src')
        """
        result = container.exec_run(f"ls -1 {directory}")

        if result.exit_code != 0:
            return []

        output = result.output.decode('utf-8')
        return [line.strip() for line in output.split('\n') if line.strip()]

    def cleanup_all_containers(self, prefix: str = 'difftesting') -> None:
        """
        Clean up all containers with a given name prefix.

        Args:
            prefix: Container name prefix to filter by

        Example:
            >>> manager.cleanup_all_containers('difftesting')
        """
        if not self.is_available():
            return

        try:
            containers = self.client.containers.list(all=True)

            for container in containers:
                if container.name.startswith(prefix):
                    print(f"Cleaning up container: {container.name}")
                    self.stop_container(container, remove=True)

        except Exception as e:
            print(f"Warning: Error during batch cleanup: {e}")
