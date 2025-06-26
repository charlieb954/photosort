"""__init__ file for photosort package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("photosort")
except PackageNotFoundError:
    # package is not installed
    pass
