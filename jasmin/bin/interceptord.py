#!/usr/bin/python3

import os
import signal
import sys
import syslog

from lockfile import FileLock, LockTimeout, AlreadyLocked
from twisted.cred import portal
from twisted.cred.checkers import AllowAnonymousAccess, InMemoryUsernamePasswordDatabaseDontUse
from twisted.internet import reactor, defer
from twisted.python import usage
from twisted.spread import pb

from jasmin.interceptor.configs import InterceptorPBConfig
from jasmin.interceptor.interceptor import InterceptorPB
from jasmin.redis.client import ConnectionWithConfiguration
from jasmin.redis.configs import RedisForJasminConfig
from jasmin.tools.cred.portal import JasminPBRealm
from jasmin.tools.spread.pb import JasminPBPortalRoot
from jasmin.config import ROOT_PATH
from jasmin.bin import BaseDaemon

CONFIG_PATH = os.getenv('CONFIG_PATH', '%s/etc/jasmin/' % ROOT_PATH)


class Options(usage.Options):
    optParameters = [
        ['config', 'c', '%s/interceptor.cfg' % CONFIG_PATH,
         'Jasmin interceptor configuration file'],
    ]


class InterceptorDaemon(BaseDaemon):
    @defer.inlineCallbacks
    def startRedisClient(self):
        """Start Redis client for interceptor scripts"""
        self._interceptor_config = InterceptorPBConfig(self.options['config'])
        if not self._interceptor_config.redis_enabled:
            return

        rc_config = RedisForJasminConfig()
        rc_config.host = self._interceptor_config.redis_host
        rc_config.port = self._interceptor_config.redis_port
        rc_config.dbid = self._interceptor_config.redis_dbid
        rc_config.password = self._interceptor_config.redis_password
        rc_config.poolsize = self._interceptor_config.redis_poolsize
        rc_config.log_level = self._interceptor_config.log_level
        rc_config.log_file = self._interceptor_config.log_file
        rc_config.log_rotate = self._interceptor_config.log_rotate
        rc_config.log_format = self._interceptor_config.log_format
        rc_config.log_date_format = self._interceptor_config.log_date_format

        self.components['rc'] = yield ConnectionWithConfiguration(rc_config)
        if rc_config.password is not None:
            yield self.components['rc'].auth(rc_config.password)
            yield self.components['rc'].select(rc_config.dbid)

    def startInterceptorPBService(self):
        """Start Interceptor PB server"""

        InterceptorPBConfigInstance = InterceptorPBConfig(self.options['config'])
        self.components['interceptor-pb-factory'] = InterceptorPB(InterceptorPBConfigInstance)

        if 'rc' in self.components:
            self.components['interceptor-pb-factory'].setRedisClient(self.components['rc'])

        # Set authentication portal
        p = portal.Portal(JasminPBRealm(self.components['interceptor-pb-factory']))
        if InterceptorPBConfigInstance.authentication:
            c = InMemoryUsernamePasswordDatabaseDontUse()
            c.addUser(InterceptorPBConfigInstance.admin_username,
                      InterceptorPBConfigInstance.admin_password)
            p.registerChecker(c)
        else:
            p.registerChecker(AllowAnonymousAccess())
        jPBPortalRoot = JasminPBPortalRoot(p)

        # Add service
        self.components['interceptor-pb-server'] = reactor.listenTCP(
            InterceptorPBConfigInstance.port,
            pb.PBServerFactory(jPBPortalRoot),
            interface=InterceptorPBConfigInstance.bind)

    def stopInterceptorPBService(self):
        """Stop Interceptor PB server"""
        return self.components['interceptor-pb-server'].stopListening()

    @defer.inlineCallbacks
    def start(self):
        """Start Interceptord daemon"""
        syslog.syslog(syslog.LOG_INFO, "Starting InterceptorPB Daemon ...")

        ########################################################
        # Start Redis client (optional)
        try:
            yield self.startRedisClient()
            if 'rc' in self.components:
                syslog.syslog(syslog.LOG_INFO, "  RedisClient Started.")
        except Exception as e:
            syslog.syslog(syslog.LOG_ERR, "  Cannot start RedisClient: %s" % e)

        ########################################################
        # Start Interceptor PB server
        try:
            yield self.startInterceptorPBService()
        except Exception as e:
            syslog.syslog(syslog.LOG_ERR, "  Cannot start Interceptor: %s" % e)
        else:
            syslog.syslog(syslog.LOG_INFO, "  Interceptor Started.")

    @defer.inlineCallbacks
    def stop(self):
        """Stop Interceptord daemon"""
        syslog.syslog(syslog.LOG_INFO, "Stopping Interceptor Daemon ...")

        if 'interceptor-pb-server' in self.components:
            yield self.stopInterceptorPBService()
            syslog.syslog(syslog.LOG_INFO, "  InterceptorPB stopped.")

        if 'rc' in self.components:
            yield self.components['rc'].disconnect()
            syslog.syslog(syslog.LOG_INFO, "  RedisClient stopped.")

        reactor.stop()

    def sighandler_stop(self, signum, frame):
        """Handle stop signal cleanly"""
        syslog.syslog(syslog.LOG_INFO, "Received signal to stop Interceptor Daemon")

        return self.stop()


if __name__ == '__main__':
    # Must not be executed simultaneously (c.f. #265)
    lock = FileLock("/tmp/interceptord")

    try:
        options = Options()
        options.parseOptions()

        # Ensure there are no paralell runs of this script
        lock.acquire(timeout=2)

        # Prepare to start
        in_d = InterceptorDaemon(options)
        # Setup signal handlers
        signal.signal(signal.SIGINT, in_d.sighandler_stop)
        signal.signal(signal.SIGTERM, in_d.sighandler_stop)
        # Start InterceptorDaemon
        in_d.start()

        reactor.run()
    except usage.UsageError as errortext:
        print('%s: %s' % (sys.argv[0], errortext))
        print('%s: Try --help for usage details.' % (sys.argv[0]))
    except LockTimeout:
        print("Lock not acquired ! exiting")
    except AlreadyLocked:
        print("There's another instance on jasmind running, exiting.")
    finally:
        # Release the lock
        if lock.i_am_locking():
            lock.release()
