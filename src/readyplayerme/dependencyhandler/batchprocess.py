from typing import List

from .interfaces import InstallerInterface


def install_dependencies(dependencies: List[InstallerInterface]):
    """Install dependencies."""
    for dependency in dependencies:
        if not dependency.is_installed():
            dependency.install()
        else:
            print(f"Dependency '{dependency.name}' is already satisfied.")
