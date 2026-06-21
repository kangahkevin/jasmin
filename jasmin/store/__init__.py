from jasmin.store.interface import StoreBackend
from jasmin.store.file import FileBackend
from jasmin.store.redisbackend import RedisBackend


def get_backend(config, redis_client=None):
    """Factory: return the configured store backend.

    When ``store_backend`` is ``redis`` but *redis_client* is not yet
    available (common during early startup), a :class:`FileBackend` is
    returned as a temporary fallback.  Call this function again once the
    Redis client is ready to obtain the real backend.
    """
    backend_type = getattr(config, 'store_backend', 'file')
    store_path = getattr(config, 'store_path', None)
    pickle_protocol = getattr(config, 'pickle_protocol', 2)

    if backend_type == 'redis' and redis_client is not None:
        prefix = getattr(config, 'store_redis_prefix', 'jasmin:')
        file_backup = getattr(config, 'store_file_backup', True)
        return RedisBackend(redis_client, prefix, pickle_protocol,
                            file_backup=file_backup, store_path=store_path)

    return FileBackend(store_path, pickle_protocol)
