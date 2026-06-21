import pickle
import time
import logging

from twisted.internet import defer

import jasmin
from jasmin.store.interface import StoreBackend
from jasmin.store.file import FileBackend

LOG_CATEGORY = "jasmin-store-redis"
log = logging.getLogger(LOG_CATEGORY)


class RedisBackend(StoreBackend):
    def __init__(self, redis_client, prefix='jasmin:', pickle_protocol=2,
                 file_backup=True, store_path=None):
        self.rc = redis_client
        self.prefix = prefix
        self.pickle_protocol = pickle_protocol
        self.file_backup = file_backup
        self._file_backend = None
        if file_backup and store_path:
            self._file_backend = FileBackend(store_path, pickle_protocol)

    def _redis_key(self, key, profile):
        return '%s%s:%s' % (self.prefix, profile, key)

    @defer.inlineCallbacks
    def save(self, key, data, profile='jcli-prod'):
        rkey = self._redis_key(key, profile)
        payload = pickle.dumps(data, self.pickle_protocol)
        log.info('Persisting [%s] to Redis key [%s]', key, rkey)
        try:
            yield self.rc.set(rkey, payload)
        except Exception as e:
            log.error('Failed persisting [%s] to Redis: %s', key, e)

        if self._file_backend:
            try:
                self._file_backend.save(key, data, profile)
            except Exception as e:
                log.warning('File backup for [%s] failed: %s', key, e)

    @defer.inlineCallbacks
    def load(self, key, profile='jcli-prod'):
        rkey = self._redis_key(key, profile)
        log.info('Loading [%s] from Redis key [%s]', key, rkey)
        try:
            payload = yield self.rc.get(rkey)
        except Exception as e:
            log.error('Failed loading [%s] from Redis: %s', key, e)
            payload = None

        if payload is not None:
            defer.returnValue(pickle.loads(payload))

        if self._file_backend:
            log.info('Redis key [%s] not found, falling back to file', rkey)
            try:
                data = self._file_backend.load(key, profile)
                yield self.save(key, data, profile)
                defer.returnValue(data)
            except Exception as e:
                log.warning('File fallback for [%s] failed: %s', key, e)

        defer.returnValue(None)
