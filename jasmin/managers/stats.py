from jasmin.tools.singleton import Singleton
from jasmin.tools.stats import Stats


class DLRLookupStatistics(Stats):
    """DLR Lookup statistics holder"""

    def __init__(self):
        self._stats = {
            'lookup_count': 0,
            'lookup_hit_count': 0,
            'lookup_miss_count': 0,
            'lookup_error_count': 0,
            'publish_http_count': 0,
            'publish_smpps_count': 0,
            'map_created_count': 0,
            'map_removed_count': 0,
            'retry_count': 0,
        }

    def getStats(self):
        return self._stats


class DLRLookupStatsCollector(metaclass=Singleton):
    """DLR Lookup statistics collection holder"""

    def get(self):
        if not hasattr(self, '_instance'):
            self._instance = DLRLookupStatistics()
        return self._instance
