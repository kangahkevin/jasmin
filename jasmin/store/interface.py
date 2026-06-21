from abc import ABC, abstractmethod


class StoreBackend(ABC):
    """Abstract interface for Jasmin configuration persistence."""

    @abstractmethod
    def save(self, key, data, profile='jcli-prod'):
        """Persist *data* (bytes) under *key* for the given *profile*."""

    @abstractmethod
    def load(self, key, profile='jcli-prod'):
        """Return the raw bytes previously saved under *key*, or None."""
