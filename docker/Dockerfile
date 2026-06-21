FROM python:3.12-slim-bookworm

LABEL maintainer="Kekantek <kangahkevinkanga@outlook.com>"

# Install requirements
RUN apt-get update && apt-get install -y \
    libffi-dev libc6-dev libpq-dev libpq5 \
    libssl-dev ca-certificates supervisor \
    cron libjemalloc2 telnet wget gcc \
    make dpkg-dev locales tzdata curl \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set Locale properly
RUN localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US.UTF-8

# Run python with jemalloc
RUN ln -sf $(find /usr/lib -name 'libjemalloc.so.2' -print -quit) /usr/local/lib/libjemalloc.so.2
ENV LD_PRELOAD=/usr/local/lib/libjemalloc.so.2

# Set Jasmin environment
ENV CONFIG_PATH=/etc/jasmin
ENV RESOURCE_PATH=/etc/jasmin/resource
ENV STORE_PATH=/etc/jasmin/store
ENV LOG_PATH=/var/log/jasmin
ENV SCRIPT_PATH=/etc/jasmin/scripts
ENV SUPERVISOR_PATH=/etc/supervisor
ENV SUPERVISOR_CONF_PATH=/etc/supervisor/conf.d
ENV CRON_PATH=/etc/jasmin/cron

ENV UNICODEMAP_JP=unicode-ascii

RUN groupadd -r jasmin && useradd -r -g jasmin jasmin
RUN mkdir -p ${CONFIG_PATH} ${RESOURCE_PATH} ${STORE_PATH} ${LOG_PATH} ${SCRIPT_PATH}

# Deploy Jasmin
WORKDIR /build
COPY . .

RUN pip install --upgrade pip setuptools \
 && pip install . \
 && pip install python-dotenv "psycopg[binary,pool]" \
 && rm -rf /build

COPY docker/config/cron ${CRON_PATH}
COPY docker/config/jasmin/*.cfg ${CONFIG_PATH}/
COPY docker/config/resource/ ${RESOURCE_PATH}/
COPY docker/config/supervisor/conf.d/ ${SUPERVISOR_CONF_PATH}/
COPY docker/config/supervisor/supervisord.conf ${SUPERVISOR_PATH}/supervisord.conf
COPY docker/config/scripts/ ${SCRIPT_PATH}/
RUN chmod +x ${SCRIPT_PATH}/*.sh

RUN chown -R jasmin:jasmin ${CONFIG_PATH} ${LOG_PATH}

COPY docker/entrypoint.sh ${CONFIG_PATH}/
RUN chmod +x ${CONFIG_PATH}/entrypoint.sh

WORKDIR /etc/jasmin

EXPOSE 2775 8990 1401 9001

VOLUME ["/var/log/jasmin", "/etc/jasmin", "/etc/jasmin/store", "/etc/jasmin/scripts", "/etc/supervisor", "/etc/supervisor/conf.d"]

ENTRYPOINT ["/etc/jasmin/entrypoint.sh"]

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
