from twisted.web.resource import Resource

from jasmin.protocols.http.stats import HttpAPIStatsCollector
from jasmin.protocols.smpp.stats import SMPPClientStatsCollector, SMPPServerStatsCollector
from jasmin.managers.stats import DLRLookupStatsCollector
from jasmin.routing.stats import (DLRThrowerStatsCollector, DeliverSmThrowerStatsCollector,
                                  RouterStatsCollector, InterceptorStatsCollector)

PROM_METRICS_HTTPAPI = {
    'request_count':            {'type': b'counter', 'help': b'Http request count.'},
    'interceptor_count':        {'type': b'counter', 'help': b'Successful http request count.'},
    'auth_error_count':         {'type': b'counter', 'help': b'Authentication error count.'},
    'route_error_count':        {'type': b'counter', 'help': b'Routing error count.'},
    'interceptor_error_count':  {'type': b'counter', 'help': b'Interceptor error count.'},
    'throughput_error_count':   {'type': b'counter', 'help': b'Throughput exceeded error count.'},
    'charging_error_count':     {'type': b'counter', 'help': b'Charging error count.'},
    'server_error_count':       {'type': b'counter', 'help': b'Server error count.'},
    'success_count':            {'type': b'counter', 'help': b'Successful http request count.'},
}
PROM_METRICS_SMPPC = {
    'connected_count':          {'type': b'counter', 'help': b'Cumulated number of successful connections.'},
    'disconnected_count':       {'type': b'counter', 'help': b'Cumulated number of disconnections.'},
    'bound_count':              {'type': b'counter', 'help': b'Number of bound sessions.'},
    'submit_sm_request_count':  {'type': b'counter', 'help': b'SubmitSm pdu requests count.'},
    'submit_sm_count':          {'type': b'counter', 'help': b'Complete SubmitSm transactions count.'},
    'deliver_sm_count':         {'type': b'counter', 'help': b'DeliverSm pdu requests count.'},
    'data_sm_count':            {'type': b'counter', 'help': b'Complete DataSm transactions count.'},
    'interceptor_count':        {'type': b'counter', 'help': b'Interceptor calls count.'},
    'elink_count':              {'type': b'counter', 'help': b'EnquireLinks count.'},
    'throttling_error_count':   {'type': b'counter', 'help': b'Throttling errors count.'},
    'interceptor_error_count':  {'type': b'counter', 'help': b'Interception errors count.'},
    'other_submit_error_count': {'type': b'counter', 'help': b'Other errors count.'},
}
PROM_METRICS_SMPPS_API = {
    'connected_count':          {'type': b'counter', 'help': b'Number of connected sessions.'},
    'connect_count':            {'type': b'counter', 'help': b'Cumulated number of connect requests.'},
    'disconnect_count':         {'type': b'counter', 'help': b'Cumulated number of disconnect requests.'},
    'interceptor_count':        {'type': b'counter', 'help': b'Interceptor calls count.'},
    'bound_trx_count':          {'type': b'counter', 'help': b'Number of bound sessions in transceiver mode.'},
    'bound_rx_count':           {'type': b'counter', 'help': b'Number of bound sessions in receiver mode.'},
    'bound_tx_count':           {'type': b'counter', 'help': b'Number of bound sessions in transmitter mode.'},
    'bind_trx_count':           {'type': b'counter', 'help': b'Number of bind requests in transceiver mode.'},
    'bind_rx_count':            {'type': b'counter', 'help': b'Number of bind requests in receiver mode.'},
    'bind_tx_count':            {'type': b'counter', 'help': b'Number of bind requests in transmitter mode.'},
    'unbind_count':             {'type': b'counter', 'help': b'Cumulated number of unbind requests.'},
    'submit_sm_request_count':  {'type': b'counter', 'help': b'SubmitSm pdu requests count.'},
    'submit_sm_count':          {'type': b'counter', 'help': b'Complete SubmitSm transactions count.'},
    'deliver_sm_count':         {'type': b'counter', 'help': b'DeliverSm pdu requests count.'},
    'data_sm_count':            {'type': b'counter', 'help': b'Complete DataSm transactions count.'},
    'elink_count':              {'type': b'counter', 'help': b'EnquireLinks count.'},
    'throttling_error_count':   {'type': b'counter', 'help': b'Throttling errors count.'},
    'interceptor_error_count':  {'type': b'counter', 'help': b'Interception errors count.'},
    'other_submit_error_count': {'type': b'counter', 'help': b'Other errors count.'},
}
PROM_METRICS_DLR_LOOKUP = {
    'lookup_count':             {'type': b'counter', 'help': b'DLR lookup requests count.'},
    'lookup_hit_count':         {'type': b'counter', 'help': b'DLR lookup successful hits count.'},
    'lookup_miss_count':        {'type': b'counter', 'help': b'DLR lookup misses (map not found) count.'},
    'lookup_error_count':       {'type': b'counter', 'help': b'DLR lookup errors count.'},
    'publish_http_count':       {'type': b'counter', 'help': b'DLR published to HTTP thrower count.'},
    'publish_smpps_count':      {'type': b'counter', 'help': b'DLR published to SMPP thrower count.'},
    'map_created_count':        {'type': b'counter', 'help': b'DLR maps created in Redis count.'},
    'map_removed_count':        {'type': b'counter', 'help': b'DLR maps removed from Redis count.'},
    'retry_count':              {'type': b'counter', 'help': b'DLR lookup retries count.'},
}
PROM_METRICS_DLR_THROWER = {
    'http_throw_count':         {'type': b'counter', 'help': b'DLR HTTP throws successful count.'},
    'http_throw_error_count':   {'type': b'counter', 'help': b'DLR HTTP throws error count.'},
    'http_throw_retry_count':   {'type': b'counter', 'help': b'DLR HTTP throws retry count.'},
    'smpps_throw_count':        {'type': b'counter', 'help': b'DLR SMPP throws successful count.'},
    'smpps_throw_error_count':  {'type': b'counter', 'help': b'DLR SMPP throws error count.'},
    'smpps_throw_retry_count':  {'type': b'counter', 'help': b'DLR SMPP throws retry count.'},
}
PROM_METRICS_DELIVERSM_THROWER = {
    'http_throw_count':         {'type': b'counter', 'help': b'DeliverSm HTTP throws successful count.'},
    'http_throw_error_count':   {'type': b'counter', 'help': b'DeliverSm HTTP throws error count.'},
    'http_throw_retry_count':   {'type': b'counter', 'help': b'DeliverSm HTTP throws retry count.'},
    'smpps_throw_count':        {'type': b'counter', 'help': b'DeliverSm SMPP throws successful count.'},
    'smpps_throw_error_count':  {'type': b'counter', 'help': b'DeliverSm SMPP throws error count.'},
    'smpps_throw_retry_count':  {'type': b'counter', 'help': b'DeliverSm SMPP throws retry count.'},
}
PROM_METRICS_ROUTER = {
    'mo_route_count':           {'type': b'counter', 'help': b'MO messages routed successfully count.'},
    'mo_route_miss_count':      {'type': b'counter', 'help': b'MO messages with no route found count.'},
    'mt_route_count':           {'type': b'counter', 'help': b'MT messages routed successfully count.'},
    'mt_route_miss_count':      {'type': b'counter', 'help': b'MT messages with no route found count.'},
    'billing_charge_count':     {'type': b'counter', 'help': b'Billing charges applied count.'},
    'billing_error_count':      {'type': b'counter', 'help': b'Billing errors (user not found) count.'},
    'billing_ack_count':        {'type': b'counter', 'help': b'Billing acks (unlimited balance) count.'},
    'billing_reject_count':     {'type': b'counter', 'help': b'Billing rejects (insufficient balance) count.'},
}
PROM_METRICS_INTERCEPTOR = {
    'script_run_count':         {'type': b'counter', 'help': b'Interceptor scripts executed count.'},
    'script_error_count':       {'type': b'counter', 'help': b'Interceptor scripts errored count.'},
    'script_slow_count':        {'type': b'counter', 'help': b'Interceptor scripts exceeding slow threshold count.'},
}


class Metrics(Resource):
    isleaf = True

    def __init__(self, SMPPClientManagerPB, log, smpps_id='smpps_01'):
        Resource.__init__(self)

        self.SMPPClientManagerPB = SMPPClientManagerPB
        self.log = log
        self.smpps_id = smpps_id

    def render_GET(self, request):
        """
        /metrics request processing, used for exporting prometheus metrics
        """

        self.log.debug("Rendering /metrics response with args: %s from %s",
                       request.args, request.getClientIP())

        request.responseHeaders.addRawHeader(b"content-type", b"text/plain")
        request.setResponseCode(200)

        # Init response payload
        response = []

        # Fill httpapi stats
        _s = HttpAPIStatsCollector().get()
        for metric, descriptor in PROM_METRICS_HTTPAPI.items():
            response.extend([
                b'# TYPE httpapi_%s %s' % (metric.encode(), descriptor['type']),
                b'# HELP httpapi_%s %s' % (metric.encode(), descriptor['help']),
                ('httpapi_%s %s' % (metric, _s.get(metric))).encode(),
            ])

        # Fill smppcs stats
        _connectors = self.SMPPClientManagerPB.perspective_connector_list()
        _stats = {}
        for metric, descriptor in PROM_METRICS_SMPPC.items():
            if len(_connectors) > 0:
                response.extend([
                    b'# TYPE smppc_%s %s' % (metric.encode(), descriptor['type']),
                    b'# HELP smppc_%s %s' % (metric.encode(), descriptor['help']),
                ])

            for _connector in _connectors:
                _cid = _connector['id']
                _s = _stats.get(_cid, SMPPClientStatsCollector().get(_cid))

                response.extend([
                    ('smppc_%s{cid="%s"} %s' % (metric, _cid, _s.get(metric))).encode(),
                ])

        # Fill smpps stats
        try:
            _s = SMPPServerStatsCollector().get(self.smpps_id).getStats()
        except Exception:
            _s = {}
        for metric, descriptor in PROM_METRICS_SMPPS_API.items():
            response.extend([
                b'# TYPE smppsapi_%s %s' % (metric.encode(), descriptor['type']),
                b'# HELP smppsapi_%s %s' % (metric.encode(), descriptor['help']),
                ('smppsapi_%s %s' % (metric, _s.get(metric, 0))).encode(),
            ])

        # Fill DLR lookup stats
        _s = DLRLookupStatsCollector().get().getStats()
        for metric, descriptor in PROM_METRICS_DLR_LOOKUP.items():
            response.extend([
                b'# TYPE dlr_lookup_%s %s' % (metric.encode(), descriptor['type']),
                b'# HELP dlr_lookup_%s %s' % (metric.encode(), descriptor['help']),
                ('dlr_lookup_%s %s' % (metric, _s.get(metric, 0))).encode(),
            ])

        # Fill DLR thrower stats
        _s = DLRThrowerStatsCollector().get().getStats()
        for metric, descriptor in PROM_METRICS_DLR_THROWER.items():
            response.extend([
                b'# TYPE dlr_thrower_%s %s' % (metric.encode(), descriptor['type']),
                b'# HELP dlr_thrower_%s %s' % (metric.encode(), descriptor['help']),
                ('dlr_thrower_%s %s' % (metric, _s.get(metric, 0))).encode(),
            ])

        # Fill DeliverSm thrower stats
        _s = DeliverSmThrowerStatsCollector().get().getStats()
        for metric, descriptor in PROM_METRICS_DELIVERSM_THROWER.items():
            response.extend([
                b'# TYPE deliversm_thrower_%s %s' % (metric.encode(), descriptor['type']),
                b'# HELP deliversm_thrower_%s %s' % (metric.encode(), descriptor['help']),
                ('deliversm_thrower_%s %s' % (metric, _s.get(metric, 0))).encode(),
            ])

        # Fill router stats
        _s = RouterStatsCollector().get().getStats()
        for metric, descriptor in PROM_METRICS_ROUTER.items():
            response.extend([
                b'# TYPE router_%s %s' % (metric.encode(), descriptor['type']),
                b'# HELP router_%s %s' % (metric.encode(), descriptor['help']),
                ('router_%s %s' % (metric, _s.get(metric, 0))).encode(),
            ])

        # Fill interceptor stats
        _s = InterceptorStatsCollector().get().getStats()
        for metric, descriptor in PROM_METRICS_INTERCEPTOR.items():
            response.extend([
                b'# TYPE interceptor_%s %s' % (metric.encode(), descriptor['type']),
                b'# HELP interceptor_%s %s' % (metric.encode(), descriptor['help']),
                ('interceptor_%s %s' % (metric, _s.get(metric, 0))).encode(),
            ])

        # Add padding
        response.extend([b'', b''])

        return b'\n'.join(response)
