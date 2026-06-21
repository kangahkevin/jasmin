#!/usr/bin/python3
# -*- coding: utf-8 -*-

import io
import os
import sys
import pickle
import logging
import txamqp.spec
import psycopg

from datetime import datetime
from dotenv import load_dotenv
from txamqp.protocol import AMQClient
from txamqp.client import TwistedDelegate
from twisted.internet import reactor, task
from twisted.internet.defer import inlineCallbacks
from twisted.internet.protocol import ClientCreator
from logging.handlers import TimedRotatingFileHandler

load_dotenv()

# Logger
logger = logging.getLogger("sms_logger")
logger.setLevel(logging.DEBUG)
handler = TimedRotatingFileHandler("/var/log/jasmin/sms_logger.log", when="midnight", backupCount=7)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Database
DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USERNAME', 'postgres')
DB_PASS = os.getenv('DB_PASSWORD', 'postgres')

# AMQP
AMQP_HOST = os.getenv('AMQP_BROKER_HOST', 'rabbitmq')
AMQP_PORT = int(os.getenv('AMQP_BROKER_PORT', 5672))
AMQP_VHOST = os.getenv('AMQP_BROKER_VHOST', '/')
AMQP_USER = os.getenv('AMQP_BROKER_USERNAME', 'guest')
AMQP_PASS = os.getenv('AMQP_BROKER_PASSWORD', 'guest')
AMQP_SPEC = '/etc/jasmin/resource/amqp0-9-1.xml'

RECONNECT_DELAY_INIT = 1
RECONNECT_DELAY_MAX = 60

ALLOWED_MODULES = frozenset({
    'jasmin', 'smpp', 'datetime',
    'builtins', '__builtin__',
    '_codecs', 'collections', 're', 'ipaddress',
})


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module.split('.')[0] in ALLOWED_MODULES:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(f"Forbidden: {module}.{name}")


def safe_unpickle(data):
    if not data:
        return None
    try:
        return RestrictedUnpickler(io.BytesIO(data)).load()
    except Exception:
        try:
            return data.decode(errors="ignore")
        except Exception:
            return data


_DC_DEFAULT_MAP = {
    'SMSC_DEFAULT_ALPHABET': 0x00, 'IA5_ASCII': 0x01, 'OCTET_UNSPECIFIED': 0x02,
    'LATIN_1': 0x03, 'OCTET_UNSPECIFIED_COMMON': 0x04, 'JIS': 0x05,
    'CYRILLIC': 0x06, 'ISO_8859_8': 0x07, 'UCS2': 0x08, 'PICTOGRAM': 0x09,
    'ISO_2022_JP': 0x0a, 'EXTENDED_KANJI_JIS': 0x0d, 'KS_C_5601': 0x0e,
}
_DC_GSM_CODING_MAP = {'DEFAULT_ALPHABET': 0x00, 'DATA_8BIT': 0x04}
_DC_GSM_CLASS_MAP = {
    'NO_MESSAGE_CLASS': 0x00, 'CLASS_1': 0x01, 'CLASS_2': 0x02, 'CLASS_3': 0x03,
}


def get_data_coding(raw):
    if raw is None:
        return 0
    if isinstance(raw, int):
        return raw
    scheme_name = getattr(getattr(raw, 'scheme', None), 'name', None)
    sd = getattr(raw, 'schemeData', None)
    if sd is None:
        return 0
    if scheme_name == 'RAW':
        return sd if isinstance(sd, int) else 0
    if scheme_name == 'GSM_MESSAGE_CLASS':
        mc = getattr(getattr(sd, 'msgCoding', None), 'name', '')
        cl = getattr(getattr(sd, 'msgClass', None), 'name', '')
        return 0xF0 | _DC_GSM_CODING_MAP.get(mc, 0) | _DC_GSM_CLASS_MAP.get(cl, 0)
    name = getattr(sd, 'name', None)
    return _DC_DEFAULT_MAP.get(name, 0) if name else 0


def get_priority(pdu_params, msg_props):
    pf = pdu_params.get("priority_flag")
    if pf is not None:
        try:
            return int(pf)
        except (ValueError, TypeError):
            pass
    return msg_props.get("priority", 0)


def parse_ts(raw):
    if isinstance(raw, datetime):
        return raw
    if raw:
        try:
            return datetime.fromisoformat(raw)
        except (ValueError, TypeError):
            pass
    return datetime.now()


def has_udhi(esm_class):
    if esm_class is None:
        return False
    if isinstance(esm_class, int):
        return bool(esm_class & 0x40)
    gf = getattr(esm_class, 'gsmFeatures', None) or set()
    return any(getattr(f, 'name', '') == 'UDHI_INDICATOR_SET' for f in gf)


def strip_udh(data):
    if not data:
        return data
    udhl = data[0]
    return data[1 + udhl:]


def extract_content(pdu):
    """Return (decoded_text, data_coding_int, pdu_count) from a PDU."""
    params = getattr(pdu, "params", {}) or {}
    dc = get_data_coding(params.get("data_coding"))
    udhi = has_udhi(params.get("esm_class"))

    parts = []
    pdu_count = 0
    cur = pdu

    while cur is not None:
        pdu_count += 1
        p = getattr(cur, "params", {}) or {}
        sm = p.get("short_message") or p.get("message_payload") or b""
        if isinstance(sm, str):
            sm = sm.encode()
        if udhi:
            sm = strip_udh(sm)
        parts.append(sm)
        cur = getattr(cur, "nextPdu", None)

    full = b"".join(parts)
    if dc == 8:
        text = full.decode('utf-16-be', errors='ignore')
    else:
        text = full.decode('utf-8', errors='ignore')

    text = text.replace('\x00', '')

    return text, dc, pdu_count


def db_connect():
    conn = psycopg.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS, autocommit=True,
    )
    logger.info("Connected to PostgreSQL (%s:%s/%s)", DB_HOST, DB_PORT, DB_NAME)
    return conn


def db_create_tables(conn):
    conn.execute("""
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

        CREATE TABLE IF NOT EXISTS mt_messages (
            id               UUID PRIMARY KEY,
            smpp_msgid       VARCHAR(64),
            uid              VARCHAR(64),
            source_connector VARCHAR(16),
            routed_cid       VARCHAR(64),
            source_addr      VARCHAR(32),
            destination_addr VARCHAR(32),
            content          TEXT,
            data_coding      INTEGER DEFAULT 0,
            pdu_count        INTEGER DEFAULT 1,
            priority         INTEGER DEFAULT 0,
            status           VARCHAR(32),
            status_code      VARCHAR(32),
            created_at       TIMESTAMP,
            submitted_at     TIMESTAMP DEFAULT NOW(),
            status_at        TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS mo_messages (
            id               UUID PRIMARY KEY,
            cid              VARCHAR(64),
            source_addr      VARCHAR(32),
            destination_addr VARCHAR(32),
            content          TEXT,
            data_coding      INTEGER DEFAULT 0,
            created_at       TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_mt_uid          ON mt_messages (uid);
        CREATE INDEX IF NOT EXISTS idx_mt_routed_cid   ON mt_messages (routed_cid);
        CREATE INDEX IF NOT EXISTS idx_mt_source_addr  ON mt_messages (source_addr);
        CREATE INDEX IF NOT EXISTS idx_mt_dest_addr    ON mt_messages (destination_addr);
        CREATE INDEX IF NOT EXISTS idx_mt_status       ON mt_messages (status);
        CREATE INDEX IF NOT EXISTS idx_mo_cid          ON mo_messages (cid);
        CREATE INDEX IF NOT EXISTS idx_mo_source_addr  ON mo_messages (source_addr);
        CREATE INDEX IF NOT EXISTS idx_mo_dest_addr    ON mo_messages (destination_addr);
        CREATE INDEX IF NOT EXISTS idx_mo_created_at   ON mo_messages (created_at);
        CREATE INDEX IF NOT EXISTS idx_mt_status_at  ON mt_messages (status_at);
    """)
    logger.info("Tables mt_messages / mo_messages ready")


# ------------------------------------------------------------------
# AMQP consumer
# ------------------------------------------------------------------

@inlineCallbacks
def gotConnection(conn, username, password):
    yield conn.start({"LOGIN": username, "PASSWORD": password})

    chan = yield conn.channel(1)
    yield chan.channel_open()

    yield chan.queue_declare(queue="sms_logger", durable=True)
    for exchange, rk in [
        ("messaging", "submit.sm.*"),
        ("messaging", "submit.sm.resp.*"),
        ("messaging", "dlr_thrower.*"),
        ("messaging", "deliver_sm_thrower.*"),
    ]:
        yield chan.queue_bind(queue="sms_logger", exchange=exchange, routing_key=rk)

    yield chan.basic_consume(queue="sms_logger", no_ack=False, consumer_tag="sms_logger")
    queue = yield conn.queue("sms_logger")

    db = db_connect()
    db_create_tables(db)

    task.LoopingCall(lambda: logger.debug("Heartbeat — OK")).start(60, now=False)

    while True:
        msg = yield queue.get()

        rk = getattr(msg, "routing_key", "")
        props = msg.content.properties or {}
        headers = props.get("headers", {}) or {}
        msgid = props.get("message-id")
        pdu = safe_unpickle(msg.content.body)

        try:
            # ── 1. submit_sm → INSERT mt_messages ────────────────────
            if rk.startswith("submit.sm.") and not rk.startswith("submit.sm.resp."):

                bill_raw = headers.get("submit_sm_resp_bill") or headers.get("submit_sm_bill")
                bill = safe_unpickle(bill_raw) if bill_raw else None
                uid = getattr(getattr(bill, "user", None), "uid", None)

                routed_cid = rk[10:]  # submit.sm.<cid>
                source_connector = headers.get("source_connector", "unknown")

                params = getattr(pdu, "params", {}) or {}
                src = params.get("source_addr", b"")
                dst = params.get("destination_addr", b"")
                source_addr = (src.decode() if isinstance(src, bytes) else str(src)).replace('\x00', '')
                dest_addr = (dst.decode() if isinstance(dst, bytes) else str(dst)).replace('\x00', '')

                content, dc, pdu_count = extract_content(pdu)
                priority = get_priority(params, props)
                created_at = parse_ts(headers.get("created_at"))

                db.execute(
                    """INSERT INTO mt_messages
                           (id, uid, source_connector, routed_cid,
                            source_addr, destination_addr,
                            content, data_coding, pdu_count, priority,
                            submitted_at, created_at)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (id) DO NOTHING""",
                    (msgid, uid, source_connector, routed_cid,
                     source_addr, dest_addr,
                     content, dc, pdu_count, priority,
                     datetime.now(), created_at),
                )

                logger.info("MT  submit_sm       [msgid:%s] [src:%s] [cid:%s] [uid:%s] [pdu:%s] [%s→%s]",
                            msgid, source_connector, routed_cid, uid,
                            pdu_count, source_addr, dest_addr)

            # ── 2. submit_sm_resp → UPDATE status + smpp_msgid ───────
            elif rk.startswith("submit.sm.resp."):

                params = getattr(pdu, "params", {}) or {}
                smpp_msgid = params.get("message_id", b"")
                if isinstance(smpp_msgid, bytes):
                    smpp_msgid = smpp_msgid.decode(errors="ignore")

                status = str(getattr(pdu, "status", "UNKNOWN")).removeprefix("CommandStatus.")

                db.execute(
                    """UPDATE mt_messages
                       SET smpp_msgid = %s, status = %s
                       WHERE id = %s""",
                    (smpp_msgid, status, msgid),
                )

                logger.info("MT  submit_sm_resp  [msgid:%s] [status:%s] [smpp:%s]",
                            msgid, status, smpp_msgid)

            # ── 3. DLR → UPDATE status + status_code + status_at
            elif rk.startswith("dlr_thrower."):

                status = headers.get("message_status", "")

                if not status.startswith("ESME_"):
                    status_code = headers.get("err", "")
                    status_at = parse_ts(headers.get("status_at"))

                    db.execute(
                        """UPDATE mt_messages
                           SET status = %s, status_code = %s,
                               status_at = %s
                           WHERE id = %s""",
                        (status, status_code, status_at, msgid),
                    )

                    logger.info("MT  DLR             [msgid:%s] [status:%s] [err:%s] [at:%s]",
                                msgid, status, status_code, status_at)

            # ── 4. deliver_sm → INSERT mo_messages ───────────────────
            elif rk.startswith("deliver_sm_thrower."):

                cid = headers.get("src-connector-id", "")

                content, dc, _ = extract_content(pdu)

                params = getattr(pdu, "params", {}) or {}
                src = params.get("source_addr", b"")
                dst = params.get("destination_addr", b"")
                source_addr = (src.decode() if isinstance(src, bytes) else str(src)).replace('\x00', '')
                dest_addr = (dst.decode() if isinstance(dst, bytes) else str(dst)).replace('\x00', '')

                db.execute(
                    """INSERT INTO mo_messages
                           (id, cid, source_addr, destination_addr,
                            content, data_coding, created_at)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (id) DO NOTHING""",
                    (msgid, cid, source_addr, dest_addr,
                     content, dc, datetime.now()),
                )

                logger.info("MO  deliver_sm      [msgid:%s] [cid:%s] [%s→%s]",
                            msgid, cid, source_addr, dest_addr)

            else:
                logger.warning("Unknown routing key: %s", rk)

        except Exception as e:
            logger.error("[%s] %s", rk, e)
            if db.closed:
                try:
                    db = db_connect()
                except Exception as re:
                    logger.error("DB reconnect failed: %s", re)

        chan.basic_ack(delivery_tag=msg.delivery_tag)


# ------------------------------------------------------------------
# Bootstrap + AMQP reconnection
# ------------------------------------------------------------------

_reconnect_delay = RECONNECT_DELAY_INIT


def main():
    global _reconnect_delay

    try:
        spec = txamqp.spec.load(AMQP_SPEC)
    except Exception as e:
        logger.error("AMQP spec error: %s", e)
        sys.exit(1)

    def connect():
        global _reconnect_delay
        logger.info("Connecting to RabbitMQ (%s:%s)", AMQP_HOST, AMQP_PORT)

        d = ClientCreator(
            reactor, AMQClient,
            delegate=TwistedDelegate(), vhost=AMQP_VHOST, spec=spec,
        ).connectTCP(AMQP_HOST, AMQP_PORT)

        def on_ok(conn):
            global _reconnect_delay
            _reconnect_delay = RECONNECT_DELAY_INIT
            logger.info("Connected to RabbitMQ")
            return gotConnection(conn, AMQP_USER, AMQP_PASS)

        def on_fail(err):
            global _reconnect_delay
            logger.error("RabbitMQ: %s — retry in %ds", err.getErrorMessage(), _reconnect_delay)
            reactor.callLater(_reconnect_delay, connect)
            _reconnect_delay = min(_reconnect_delay * 2, RECONNECT_DELAY_MAX)

        d.addCallback(on_ok)
        d.addErrback(on_fail)

    connect()


if __name__ == "__main__":
    main()
    reactor.run()
