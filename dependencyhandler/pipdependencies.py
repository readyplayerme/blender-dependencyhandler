"""Manage dependencies for the runtime environment."""

import contextlib
import importlib
import importlib.util
import subprocess
import sys
from typing import List, Optional

import pkg_resources

from .interfaces import InstallerInterface, LoaderInterface


class PipDependency(InstallerInterface, LoaderInterface):
    """Dependency installed via pip from PYPI."""

    def __init__(self, name: str, *args, package: Optional[str] = None, destination: Optional[str] = None, **kwargs):
        """Initialize the dependency class.

        :param name: Module name to import.
        :param package: The name of the package to install if different from module name.
        :param destination: The destination path to install the package to.
        """
        super().__init__(name, *args, **kwargs)
        self.package = package
        self.destination = destination

    def is_loaded(self) -> bool:
        """Check if a dependency is loaded."""
        return self.name in sys.modules  # TODO Purpose of is_loaded. Doesn't mean it's imported. Check in globals()?

    def load(self):
        """Load a dependency."""
        if self.is_loaded():
            return
        if (spec := importlib.util.find_spec(self.name)) and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[self.name] = module
            spec.loader.exec_module(module)

    def unload(self):
        """Unload a dependency."""
        with contextlib.suppress(KeyError):
            sys.modules.pop(self.name)
        importlib.invalidate_caches()

    def reload(self):
        """Reload a dependency."""
        try:
            importlib.reload(sys.modules[self.name])
        except KeyError:
            self.load()

    def is_installed(self) -> bool:
        """Check if a dependency is installed."""
        return importlib.util.find_spec(self.name) is not None

    def install(self):
        """Install a dependency.

        Raises RuntimeError.
        """
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", self.package or self.name]
                + ["--target", self.destination] * bool(self.destination),
                universal_newlines=True,
                # Blender startup is blocked during installation.
                # CREATE_NEW_CONSOLE creates a new console to show progress to the user.
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to install dependency '{self.name}'") from e
        importlib.invalidate_caches()

    def uninstall(self):
        """Uninstall a dependency."""
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", self.name])
        importlib.invalidate_caches()

    def update(self):
        """Update a dependency."""
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", self.name])


class PipPathDependency(PipDependency):
    """Dependency installed via pip from a path, either file-path, URL, or VCS."""

    def __init__(self, name: str, path: str, *args, **kwargs):
        """Initialize a dependency class.

        :param name: Module to import.
        :param path: The path to install from. Can be local file system, URL, or VCS path.
        """
        super().__init__(name, *args, **kwargs)
        self.path = path

    def install(self):
        """Install a dependency.

        Raises RuntimeError.
        """
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", self.path]
                + ["--target", self.destination] * bool(self.destination),
                universal_newlines=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to install dependency '{self.name}'") from e
        importlib.invalidate_caches()


class PipTxtDependency(InstallerInterface, LoaderInterface):
    """Loader for dependencies installed via pip from a text-file like requirements.txt.

    The text has to conform to PEP 508.
    """

    def __init__(self, name: str, path: str, *args, destination: Optional[str] = None, **kwargs):
        """Initialize the dependency class.

        :param name: Name of the collection of requirements to import.
        :param path: The path to the text file containing the requirements to install from.
        :param destination: The destination path to install the packages to.
        """
        super().__init__(name, *args, **kwargs)
        self.path = path
        self.destination = destination
        self._requirements = list(self._parse_requirements(self._read_requirements_file()))

    def _read_requirements_file(self) -> List[str]:
        """Read the requirements file."""
        with open(self.path) as f:
            # Filter out empty lines and comments.
            return [line for line in f.readlines() if (not line.startswith("#")) and line.strip()]

    def _parse_requirements(self, requirements: List[str]):
        """Parse the requirements specs and return requirement objects.

        :param requirements: The requirements to parse as strings.
        """
        # FIXME: If the project name is not the same as the name of the package to be loaded or imported, this fails.
        parsed = pkg_resources.parse_requirements(requirements)
        for requirement in parsed:
            if requirement.url:
                yield PipPathDependency(requirement.project_name, requirement.url, destination=self.destination)
            else:
                version = "".join(requirement.specs[0] if requirement.specs else ())  # Specs contain version info.
                yield PipDependency(
                    name=requirement.project_name,
                    package=requirement.project_name + version,
                    destination=self.destination,
                )

    def is_loaded(self) -> bool:
        """Check if the dependencies are loaded."""
        return all(requirement.name in sys.modules for requirement in self._requirements)

    def load(self):
        """Load the dependencies."""
        if self.is_loaded():
            return
        for requirement in self._requirements:
            if not requirement.is_loaded():
                requirement.load()

    def unload(self):
        """Unload a dependency."""
        for requirement in self._requirements:
            requirement.unload()

    def reload(self):
        """Reload dependencies."""
        for requirement in self._requirements:
            try:
                requirement.reload()
            except KeyError:
                requirement.load()

    def is_installed(self) -> bool:
        """Check if a dependency is installed."""
        return all(requirement.is_installed() for requirement in self._requirements)

    def install(self):
        """Install a dependency."""
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", self.path]
                + ["--target", self.destination] * bool(self.destination),
                universal_newlines=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to install dependencies from '{self.path}'") from e
        importlib.invalidate_caches()

    def uninstall(self):
        """Uninstall a dependency."""
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-r", self.path])
        importlib.invalidate_caches()

    def update(self):
        """Update unpinned dependencies."""
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "-r", self.path])
