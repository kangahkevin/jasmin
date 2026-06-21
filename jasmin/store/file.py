import pickle
import time
import logging

import jasmin
from jasmin.store.interface import StoreBackend
from jasmin.tools.migrations.configuration import ConfigurationMigrator

LOG_CATEGORY = "jasmin-store-file"
log = logging.getLogger(LOG_CATEGORY)


def _header():
    return ('Persisted on %s [Jasmin %s]\n' % (
        time.strftime("%c"), jasmin.get_release())).encode('ascii')


class FileBackend(StoreBackend):
    def __init__(self, store_path, pickle_protocol=2):
        self.store_path = store_path
        self.pickle_protocol = pickle_protocol

    def _path(self, key, profile):
        return '%s/%s.%s' % (self.store_path, profile, key)

    def save(self, key, data, profile='jcli-prod'):
        path = self._path(key, profile)
        log.info('Persisting [%s] to %s', key, path)
        with open(path, 'wb') as fh:
            fh.write(_header())
            fh.write(pickle.dumps(data, self.pickle_protocol))

    def load(self, key, profile='jcli-prod'):
        path = self._path(key, profile)
        log.info('Loading [%s] from %s', key, path)
        with open(path, 'rb') as fh:
            lines = fh.readlines()
        header = lines[0].decode('ascii')
        raw = b''.join(lines[1:])
        cf = ConfigurationMigrator(context=key, header=header, data=raw)
        return cf.getMigratedData()
