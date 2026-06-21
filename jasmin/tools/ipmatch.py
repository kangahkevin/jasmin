"""IP whitelist matching using the stdlib `ipaddress` module.

A *whitelist* is a string — a comma-separated list of IPv4/IPv6 addresses
and/or CIDR networks. Whitespace around entries is tolerated. Examples::

    '0.0.0.0/0,::/0'                  -> any IPv4 + IPv6 (default "allow all")
    '::/0'                            -> any IPv6
    '10.0.0.0/8'                      -> one /8 network
    '10.0.0.0/8, 192.168.1.5'         -> network + single host
    '10.0.0.0/8, 2001:db8::/32'       -> mixed v4+v6

An empty or `None` whitelist is treated as "nothing allowed".

The parser is tolerant and safe: any malformed entry is ignored (not
raised). This is deliberate — a bad config row should not silently crash
an authentication path. The caller can use :func:`validate_whitelist` at
config-set time to surface errors to the operator.
"""

from __future__ import annotations

import ipaddress
from typing import Iterable


def _split(whitelist: str | None) -> list[str]:
    if not whitelist:
        return []
    return [p.strip() for p in str(whitelist).split(',') if p.strip()]


def _parse_networks(whitelist: str | None) -> list:
    """Return a list of `IPv4Network` / `IPv6Network` parsed from the
    whitelist string. Malformed entries are skipped silently.
    """
    out = []
    for entry in _split(whitelist):
        try:
            out.append(ipaddress.ip_network(entry, strict=False))
        except (ValueError, TypeError):
            continue
    return out


def validate_whitelist(whitelist: str | None) -> tuple[bool, str | None]:
    """Validate a whitelist string. Returns ``(ok, error_message_or_None)``.

    An empty string / None is treated as an error (set `0.0.0.0/0,::/0`
    explicitly to allow everything). This helps the operator avoid accidentally
    locking themselves out by clearing the field.
    """
    parts = _split(whitelist)
    if not parts:
        return False, 'whitelist is empty (use "0.0.0.0/0,::/0" to allow any IPv4+IPv6)'
    for entry in parts:
        try:
            ipaddress.ip_network(entry, strict=False)
        except (ValueError, TypeError) as e:
            return False, 'invalid entry %r: %s' % (entry, e)
    return True, None


def parse_networks(whitelist: str | None) -> list:
    """Public wrapper around ``_parse_networks`` for pre-parsing at config time."""
    return _parse_networks(whitelist)


def is_ip_allowed(ip: str | None, whitelist: str | None = None,
                  *, networks: list | None = None) -> bool:
    """Return True if *ip* falls inside any network in *whitelist*.

    *ip* may be an IPv4 or IPv6 address as a string (e.g. what
    ``transport.getPeer().host`` gives you).

    Pass *networks* (a pre-parsed list from :func:`parse_networks`) to
    skip re-parsing the whitelist string on every call.  If both
    *whitelist* and *networks* are given, *networks* takes precedence.
    """
    if not ip:
        return False
    nets = networks if networks is not None else _parse_networks(whitelist)
    if not nets:
        return False
    try:
        addr = ipaddress.ip_address(ip)
    except (ValueError, TypeError):
        return False
    for net in nets:
        try:
            if addr.version != net.version:
                continue
            if addr in net:
                return True
        except (ValueError, TypeError):
            continue
    return False
