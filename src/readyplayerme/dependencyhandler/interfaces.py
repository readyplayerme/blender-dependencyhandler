"""Abstract classes that document what methods are required of objects returned by classes using these interfaces."""
from abc import ABC, abstractmethod
from typing import List


class LoaderInterface(ABC):
    """Abstract interface base class for loading a dependency."""

    def __init__(self, name: str, *args, **kwargs):
        """Initialize the Loader class."""
        self.name = name

    @abstractmethod
    def load(self):
        """Load a dependency."""
        pass

    @abstractmethod
    def unload(self):
        """Unload a dependency."""
        pass

    @abstractmethod
    def reload(self):
        """Reload a dependency."""
        pass

    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if a dependency is loaded."""
        pass


class InstallerInterface(ABC):
    """Abstract interface base class for installing a dependency."""

    def __init__(self, name: str, *args, **kwargs):
        """Initialize the Installer class."""
        self.name = name

    @abstractmethod
    def is_installed(self) -> bool:
        """Check if a dependency is installed."""
        pass

    @abstractmethod
    def install(self):
        """Install a dependency."""
        pass

    @abstractmethod
    def uninstall(self):
        """Uninstall a dependency."""
        pass

    @abstractmethod
    def update(self):
        """Update a dependency."""
        pass


class ListerInterface(ABC):
    """Abstract base class for dependency listers."""

    @abstractmethod
    def list(self) -> list:
        """List all dependencies."""
        pass

    @abstractmethod
    def list_installed(self) -> List:
        """List all installed dependencies."""
        pass

    @abstractmethod
    def list_loaded(self) -> List:
        """List all loaded dependencies."""
        pass
