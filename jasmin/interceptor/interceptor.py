import pickle
import datetime as dt
import sys
import logging
from logging.handlers import TimedRotatingFileHandler

from twisted.spread import pb

from jasmin.tools.eval import CompiledNode
from jasmin.routing.stats import InterceptorStatsCollector

LOG_CATEGORY = "jasmin-interceptor-pb"

_SAFE_BUILTINS = {
    k: __builtins__[k] if isinstance(__builtins__, dict) else getattr(__builtins__, k)
    for k in (
        'True', 'False', 'None',
        'abs', 'all', 'any', 'bin', 'bool', 'bytes', 'bytearray',
        'chr', 'complex', 'dict', 'divmod', 'enumerate', 'filter',
        'float', 'format', 'frozenset', 'getattr', 'hasattr', 'hash',
        'hex', 'int', 'isinstance', 'issubclass', 'iter', 'len', 'list',
        'map', 'max', 'min', 'next', 'oct', 'ord', 'pow', 'print',
        'range', 'repr', 'reversed', 'round', 'set', 'slice', 'sorted',
        'str', 'sum', 'tuple', 'type', 'zip',
    )
}


class InterceptorPB(pb.Avatar):
    def __init__(self, InterceptorPBConfig):
        self.config = InterceptorPBConfig
        self.avatar = None
        self.redisClient = None
        self.stats = InterceptorStatsCollector().get()

        # Set up a dedicated logger
        self.log = logging.getLogger(LOG_CATEGORY)
        if len(self.log.handlers) != 1:
            self.log.setLevel(self.config.log_level)
            if 'stdout' in self.config.log_file:
                handler = logging.StreamHandler(sys.stdout)
            else:
                handler = TimedRotatingFileHandler(filename=self.config.log_file, when=self.config.log_rotate)
            formatter = logging.Formatter(self.config.log_format, self.config.log_date_format)
            handler.setFormatter(formatter)
            self.log.addHandler(handler)
            self.log.propagate = False

        self.log.info('Interceptor configured and ready.')

    def setRedisClient(self, redisClient):
        self.redisClient = redisClient
        self.log.info('Added Redis client to InterceptorPB')

    def setAvatar(self, avatar):
        if isinstance(avatar, str):
            self.log.info('Authenticated Avatar: %s', avatar)
        else:
            self.log.info('Anonymous connection')

        self.avatar = avatar

    def perspective_run_script(self, pyCode, routable):
        """Will execute pyCode with the routable argument"""
        routable = pickle.loads(routable)
        smpp_status = http_status = None

        try:
            self.log.info('Running with a %s (from:%s, to:%s).',
                          routable.pdu.id,
                          routable.pdu.params['source_addr'],
                          routable.pdu.params['destination_addr'])
            self.log.debug('Running [%s]', pyCode)
            self.log.debug('... having routable with pdu: %s', routable.pdu)
            node = CompiledNode().get(pyCode)
            script_globals = {
                '__builtins__': _SAFE_BUILTINS,
                'hashlib': __import__('hashlib'),
                're': __import__('re'),
                'json': __import__('json'),
                'datetime': __import__('datetime'),
                'math': __import__('math'),
                'struct': __import__('struct'),
            }
            script_locals = {
                'routable': routable,
                'smpp_status': smpp_status,
                'http_status': http_status,
                'extra': {},
                'rc': self.redisClient,
            }

            # Run script and measure execution time
            start = dt.datetime.now()
            eval(node, script_globals, script_locals)
            end = dt.datetime.now()
            delay = (end - start).total_seconds()
            self.log.debug('... took %s seconds.', delay)
        except Exception as e:
            self.stats.inc('script_error_count')
            self.log.error('Executing script on routable (from:%s, to:%s) returned: %s',
                           routable.pdu.params.get('source_addr', '?'),
                           routable.pdu.params.get('destination_addr', '?'),
                           '%s: %s' % (type(e), e))
            return False
        else:
            self.stats.inc('script_run_count')
            if 0 <= self.config.log_slow_script <= delay:
                self.stats.inc('script_slow_count')
                self.log.warning('Execution delay [%ss] for script [%s].', delay, pyCode)

            if script_locals['smpp_status'] is None and script_locals['http_status'] is None:
                return pickle.dumps(script_locals['routable'], pickle.HIGHEST_PROTOCOL)
            else:
                # If we have one of the statuses set to non-zero value
                #  then both of them must be non-zero to avoid misbehaviour
                #  of differents apis: if we return an error in smpp, we must
                #  do the same in http as well.
                if script_locals['smpp_status'] is None or not isinstance(script_locals['smpp_status'], int):
                    # ESME_RUNKNOWNERR
                    self.log.info(
                        'Setting smpp_status to 255 when having http_status = %s and smpp_status = %s.',
                        script_locals['http_status'],
                        script_locals['smpp_status'])
                    script_locals['smpp_status'] = 255
                elif script_locals['http_status'] is None or not isinstance(script_locals['http_status'], int):
                    # Unknown Error
                    self.log.info(
                        'Setting http_status to 520 when having smpp_status = %s and http_status = %s.',
                        script_locals['smpp_status'],
                        script_locals['http_status'])
                    script_locals['http_status'] = 520

                r = {'http_status': script_locals['http_status'],
                     'smpp_status': script_locals['smpp_status'],
                     'extra': script_locals['extra']}
                self.log.info('Returning statuses: %s', r)
                return r
