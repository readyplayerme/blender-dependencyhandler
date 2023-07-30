"""This module provides functionality to batch process dependencies."""
import logging

from readyplayerme.dependencyhandler.interfaces import InstallerInterface

logger = logging.getLogger(__name__)


def install_dependencies(dependencies: list[InstallerInterface]):
    """Install dependencies."""
    for dependency in dependencies:
        if not dependency.is_installed():
            dependency.install()
        else:
            logger.info("Dependency '%s' is already satisfied.", dependency.name)
