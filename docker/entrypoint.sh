#!/bin/bash
set -e

# Clean lock files
echo 'Cleaning lock files'
rm -f /tmp/*.lock

if [ "$AMQP_BROKER_VHOST" != "/" ]; then
  curl -u $AMQP_BROKER_USERNAME:$AMQP_BROKER_PASSWORD -X PUT http://$AMQP_BROKER_HOST:$AMQP_BROKER_MANAGEMENT_PORT/api/vhosts/$AMQP_BROKER_VHOST
fi

# Cron
cat /etc/jasmin/cron/crontab >> /etc/cron.d/jasmin
chmod 0644 /etc/cron.d/jasmin
crontab /etc/cron.d/jasmin

# supervisor

## inet_http_server
sed -i "/\[inet_http_server\]/,/port/ s|port.*|port=$SUPERVISOR_HOST:$SUPERVISOR_PORT|" /etc/supervisor/supervisord.conf
sed -i "/\[inet_http_server\]/,/username/ s|username.*|username=$SUPERVISOR_USERNAME|" /etc/supervisor/supervisord.conf
sed -i "/\[inet_http_server\]/,/password/ s|password.*|password=$SUPERVISOR_PASSWORD|" /etc/supervisor/supervisord.conf

## supervisorctl
sed -i "/\[supervisorctl\]/,/serverurl/ s|serverurl.*|serverurl=$SUPERVISOR_SERVER_URL|" /etc/supervisor/supervisord.conf

# dlr.cfg

## smpp-server-pb-client
sed -i "/\[smpp-server-pb-client\]/,/host/ s|host.*|host = $SMPP_SERVER_PB_BIND|" /etc/jasmin/dlr.cfg
sed -i "/\[smpp-server-pb-client\]/,/port/ s|port.*|port = $SMPP_SERVER_PB_PORT|" /etc/jasmin/dlr.cfg

## amqp-broker
sed -i "/\[amqp-broker\]/,/host/ s|host.*|host = $AMQP_BROKER_HOST|" /etc/jasmin/dlr.cfg
sed -i "/\[amqp-broker\]/,/port/ s|port.*|port = $AMQP_BROKER_PORT|" /etc/jasmin/dlr.cfg
sed -i "/\[amqp-broker\]/,/vhost/ s|vhost.*|vhost = $AMQP_BROKER_VHOST|" /etc/jasmin/dlr.cfg
sed -i "/\[amqp-broker\]/,/username/ s|username.*|username = $AMQP_BROKER_USERNAME|" /etc/jasmin/dlr.cfg
sed -i "/\[amqp-broker\]/,/password/ s|password.*|password = $AMQP_BROKER_PASSWORD|" /etc/jasmin/dlr.cfg

# dlrlookup.cfg

## redis-client
sed -i "/\[redis-client\]/,/host/ s|host.*|host = $REDIS_HOST|" /etc/jasmin/dlrlookup.cfg
sed -i "/\[redis-client\]/,/port/ s|port.*|port = $REDIS_PORT|" /etc/jasmin/dlrlookup.cfg
sed -i "/\[redis-client\]/,/dbid/ s|dbid.*|dbid = $REDIS_DBID|" /etc/jasmin/dlrlookup.cfg
sed -i "/\[redis-client\]/,/password/ s|password.*|password = $REDIS_PASSWORD|" /etc/jasmin/dlrlookup.cfg

## amqp-broker
sed -i "/\[amqp-broker\]/,/host/ s|host.*|host = $AMQP_BROKER_HOST|" /etc/jasmin/dlrlookup.cfg
sed -i "/\[amqp-broker\]/,/port/ s|port.*|port = $AMQP_BROKER_PORT|" /etc/jasmin/dlrlookup.cfg
sed -i "/\[amqp-broker\]/,/vhost/ s|vhost.*|vhost = $AMQP_BROKER_VHOST|" /etc/jasmin/dlrlookup.cfg
sed -i "/\[amqp-broker\]/,/username/ s|username.*|username = $AMQP_BROKER_USERNAME|" /etc/jasmin/dlrlookup.cfg
sed -i "/\[amqp-broker\]/,/password/ s|password.*|password = $AMQP_BROKER_PASSWORD|" /etc/jasmin/dlrlookup.cfg

# interceptor.cfg

## interceptor
sed -i "/\[interceptor\]/,/bind/ s|bind.*|bind = $INTERCEPTOR_BIND|" /etc/jasmin/interceptor.cfg
sed -i "/\[interceptor\]/,/port/ s|port.*|port = $INTERCEPTOR_PORT|" /etc/jasmin/interceptor.cfg

## redis-client
sed -i "/\[redis-client\]/,/host/ s|host.*|host = $REDIS_HOST|" /etc/jasmin/interceptor.cfg
sed -i "/\[redis-client\]/,/port/ s|port.*|port = $REDIS_PORT|" /etc/jasmin/interceptor.cfg
sed -i "/\[redis-client\]/,/dbid/ s|dbid.*|dbid = $REDIS_INTERCEPTOR_DBID|" /etc/jasmin/interceptor.cfg
sed -i "/\[redis-client\]/,/password/ s|password.*|password = $REDIS_PASSWORD|" /etc/jasmin/interceptor.cfg

# jasmin.cfg

## smpp-server
sed -i "/\[smpp-server\]/,/id/ s|id.*|id = $SMPP_SERVER_ID|" /etc/jasmin/jasmin.cfg
sed -i "/\[smpp-server\]/,/bind/ s|bind.*|bind = $SMPP_SERVER_BIND|" /etc/jasmin/jasmin.cfg
sed -i "/\[smpp-server\]/,/port/ s|port.*|port = $SMPP_SERVER_PORT|" /etc/jasmin/jasmin.cfg

## smpp-server-pb
sed -i "/\[smpp-server-pb\]/,/bind/ s|bind.*|bind = $SMPP_SERVER_PB_BIND|" /etc/jasmin/jasmin.cfg
sed -i "/\[smpp-server-pb\]/,/port/ s|port.*|port = $SMPP_SERVER_PB_PORT|" /etc/jasmin/jasmin.cfg

## client-management
sed -i "/\[client-management\]/,/bind/ s|bind.*|bind = $CLIENT_MANAGEMENT_BIND|" /etc/jasmin/jasmin.cfg
sed -i "/\[client-management\]/,/port/ s|port.*|port = $CLIENT_MANAGEMENT_PORT|" /etc/jasmin/jasmin.cfg

## http-api
sed -i "/\[http-api\]/,/bind/ s|bind.*|bind = $HTTP_API_BIND|" /etc/jasmin/jasmin.cfg
sed -i "/\[http-api\]/,/port/ s|port.*|port = $HTTP_API_PORT|" /etc/jasmin/jasmin.cfg

## router
sed -i "/\[router\]/,/bind/ s|bind.*|bind = $ROUTER_BIND|" /etc/jasmin/jasmin.cfg
sed -i "/\[router\]/,/port/ s|port.*|port = $ROUTER_PORT|" /etc/jasmin/jasmin.cfg

## jcli
sed -i "/\[jcli\]/,/bind/ s|bind.*|bind = $JCLI_BIND|" /etc/jasmin/jasmin.cfg
sed -i "/\[jcli\]/,/port/ s|port.*|port = $JCLI_PORT|" /etc/jasmin/jasmin.cfg

## interceptor-client
sed -i "/\[interceptor-client\]/,/host/ s|host.*|host = $INTERCEPTOR_BIND|" /etc/jasmin/jasmin.cfg
sed -i "/\[interceptor-client\]/,/port/ s|port.*|port = $INTERCEPTOR_PORT|" /etc/jasmin/jasmin.cfg

## redis-client
sed -i "/\[redis-client\]/,/host/ s|host.*|host = $REDIS_HOST|" /etc/jasmin/jasmin.cfg
sed -i "/\[redis-client\]/,/port/ s|port.*|port = $REDIS_PORT|" /etc/jasmin/jasmin.cfg
sed -i "/\[redis-client\]/,/dbid/ s|dbid.*|dbid = $REDIS_DBID|" /etc/jasmin/jasmin.cfg
sed -i "/\[redis-client\]/,/password/ s|password.*|password = $REDIS_PASSWORD|" /etc/jasmin/jasmin.cfg

## amqp-broker
sed -i "/\[amqp-broker\]/,/host/ s|host.*|host = $AMQP_BROKER_HOST|" /etc/jasmin/jasmin.cfg
sed -i "/\[amqp-broker\]/,/port/ s|port.*|port = $AMQP_BROKER_PORT|" /etc/jasmin/jasmin.cfg
sed -i "/\[amqp-broker\]/,/vhost/ s|vhost.*|vhost = $AMQP_BROKER_VHOST|" /etc/jasmin/jasmin.cfg
sed -i "/\[amqp-broker\]/,/username/ s|username.*|username = $AMQP_BROKER_USERNAME|" /etc/jasmin/jasmin.cfg
sed -i "/\[amqp-broker\]/,/password/ s|password.*|password = $AMQP_BROKER_PASSWORD|" /etc/jasmin/jasmin.cfg

echo 'Start Cron'
cron

# If RestAPI http Mode, start Guicorn
if [ "$RESTAPI_HTTP_MODE" = 1 ]; then
  # start restapi
  exec gunicorn -b 0.0.0.0:8080 jasmin.protocols.rest:api --access-logfile /var/log/jasmin/rest-api.access.log --disable-redirect-access-to-syslog

# If Celery Worker is enabled, start Celery worker
elif [ "$RESTAPI_WORKER_MODE" = 1 ]; then
  echo 'Starting Celery worker'
  exec celery -A jasmin.protocols.rest.tasks worker -l INFO -c 4 --autoscale=10,3

else
  exec "$@"
fi
