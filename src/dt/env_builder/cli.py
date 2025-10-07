"""
CLI tool for environment builder operations.
"""

import click
import sys
from pathlib import Path

from .dependency_scanner import DependencyScanner
from .env_orchestrator import EnvironmentOrchestrator
from .docker_manager import DockerConfig


@click.group()
def cli():
    """Environment Builder CLI for differential testing."""
    pass


@cli.command()
@click.option('--file-a', '-a', required=True, help='Path to version A file')
@click.option('--file-b', '-b', required=True, help='Path to version B file')
@click.option('--project-root', '-p', help='Project root directory')
@click.option('--output', '-o', default='requirements_discovered.txt',
              help='Output file for requirements')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def scan(file_a, file_b, project_root, output, verbose):
    """Scan files for dependencies."""
    click.echo("🔍 Scanning dependencies...")

    scanner = DependencyScanner()

    # Scan the files
    deps = scanner.scan_project(
        project_root=project_root or '.',
        file_a=file_a,
        file_b=file_b
    )

    # Display results
    click.echo(f"\n📊 Scan Results:")
    click.echo(f"  Standard library modules: {len(deps.stdlib_modules)}")
    click.echo(f"  Third-party packages: {len(deps.third_party_packages)}")
    click.echo(f"  Local imports: {len(deps.local_imports)}")

    if verbose:
        if deps.stdlib_modules:
            click.echo(f"\n  Standard library: {', '.join(sorted(deps.stdlib_modules))}")
        if deps.third_party_packages:
            click.echo(f"\n  Third-party: {', '.join(sorted(deps.third_party_packages))}")
        if deps.local_imports:
            click.echo(f"\n  Local: {', '.join(sorted(deps.local_imports))}")

    # Generate requirements file
    requirements = scanner.get_install_requirements(deps)

    if requirements:
        scanner.generate_requirements_txt(deps, output)
        click.echo(f"\n✅ Generated {output} with {len(requirements)} packages")
    else:
        click.echo("\n⚠️  No third-party packages found")


@cli.command()
@click.option('--file-a', '-a', required=True, help='Path to version A file')
@click.option('--file-b', '-b', required=True, help='Path to version B file')
@click.option('--docker/--no-docker', default=True, help='Use Docker isolation')
@click.option('--image-name', default='difftest-env', help='Docker image name')
@click.option('--container-name', default='difftest-runner', help='Docker container name')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def setup(file_a, file_b, docker, image_name, container_name, verbose):
    """Set up testing environment."""
    click.echo("🔧 Setting up environment...")

    # Configure Docker
    docker_config = DockerConfig(
        image_name=image_name,
        container_name=container_name
    ) if docker else None

    # Create orchestrator
    orchestrator = EnvironmentOrchestrator(
        docker_config=docker_config,
        use_docker=docker
    )

    # Set up environment
    env_setup = orchestrator.setup_environment(
        file_a=file_a,
        file_b=file_b
    )

    if env_setup.success:
        click.echo("✅ Environment setup complete!")

        if env_setup.container_id:
            click.echo(f"   Container ID: {env_setup.container_id[:12]}")

        if env_setup.requirements:
            click.echo(f"   Installed packages: {len(env_setup.requirements)}")

            if verbose:
                click.echo(f"   Packages: {', '.join(env_setup.requirements)}")

        if env_setup.dependencies and verbose:
            report = orchestrator.get_dependency_report(env_setup.dependencies)
            click.echo(f"\n{report}")

    else:
        click.echo(f"❌ Environment setup failed: {env_setup.error_message}")
        sys.exit(1)


@cli.command()
@click.option('--container-id', '-c', help='Container ID to cleanup')
@click.option('--container-name', default='difftest-runner', help='Container name')
def cleanup(container_id, container_name):
    """Clean up Docker resources."""
    from .docker_manager import DockerManager

    click.echo("🧹 Cleaning up resources...")

    docker_manager = DockerManager()
    cid = container_id or container_name

    docker_manager.cleanup(cid)
    click.echo("✅ Cleanup complete")


@cli.command()
def check():
    """Check if Docker is available."""
    from .docker_manager import DockerManager

    docker_manager = DockerManager()

    if docker_manager.check_docker_available():
        click.echo("✅ Docker is available")

        # Get Docker version
        import subprocess
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True
        )
        click.echo(f"   {result.stdout.strip()}")
    else:
        click.echo("❌ Docker is not available")
        sys.exit(1)


if __name__ == '__main__':
    cli()
