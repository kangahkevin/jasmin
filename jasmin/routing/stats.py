from jasmin.tools.singleton import Singleton
from jasmin.tools.stats import Stats


class DLRThrowerStatistics(Stats):
    """DLR Thrower statistics holder"""

    def __init__(self):
        self._stats = {
            'http_throw_count': 0,
            'http_throw_error_count': 0,
            'http_throw_retry_count': 0,
            'smpps_throw_count': 0,
            'smpps_throw_error_count': 0,
            'smpps_throw_retry_count': 0,
        }

    def getStats(self):
        return self._stats


class DeliverSmThrowerStatistics(Stats):
    """DeliverSm Thrower statistics holder"""

    def __init__(self):
        self._stats = {
            'http_throw_count': 0,
            'http_throw_error_count': 0,
            'http_throw_retry_count': 0,
            'smpps_throw_count': 0,
            'smpps_throw_error_count': 0,
            'smpps_throw_retry_count': 0,
        }

    def getStats(self):
        return self._stats


class RouterStatistics(Stats):
    """Router statistics holder"""

    def __init__(self):
        self._stats = {
            'mo_route_count': 0,
            'mo_route_miss_count': 0,
            'mt_route_count': 0,
            'mt_route_miss_count': 0,
            'billing_charge_count': 0,
            'billing_error_count': 0,
            'billing_ack_count': 0,
            'billing_reject_count': 0,
        }

    def getStats(self):
        return self._stats


class InterceptorStatistics(Stats):
    """Interceptor statistics holder"""

    def __init__(self):
        self._stats = {
            'script_run_count': 0,
            'script_error_count': 0,
            'script_slow_count': 0,
        }

    def getStats(self):
        return self._stats


class DLRThrowerStatsCollector(metaclass=Singleton):
    """DLR Thrower statistics collection holder"""

    def get(self):
        if not hasattr(self, '_instance'):
            self._instance = DLRThrowerStatistics()
        return self._instance


class DeliverSmThrowerStatsCollector(metaclass=Singleton):
    """DeliverSm Thrower statistics collection holder"""

    def get(self):
        if not hasattr(self, '_instance'):
            self._instance = DeliverSmThrowerStatistics()
        return self._instance


class RouterStatsCollector(metaclass=Singleton):
    """Router statistics collection holder"""

    def get(self):
        if not hasattr(self, '_instance'):
            self._instance = RouterStatistics()
        return self._instance


class InterceptorStatsCollector(metaclass=Singleton):
    """Interceptor statistics collection holder"""

    def get(self):
        if not hasattr(self, '_instance'):
            self._instance = InterceptorStatistics()
        return self._instance
