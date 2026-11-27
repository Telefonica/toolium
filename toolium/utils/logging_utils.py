"""Logging helpers."""

import logging
import re

_UNICODE_ESCAPE = re.compile(r'\\u([0-9a-fA-F]{4})|\\U([0-9a-fA-F]{8})')


def decode_unicode_escapes(message):
    """Decode literal Unicode escapes while leaving other backslashes unchanged."""
    decoded = _UNICODE_ESCAPE.sub(lambda match: chr(int(match.group(1) or match.group(2), 16)), message)
    return decoded.encode('utf-16', 'surrogatepass').decode('utf-16')


class UnicodeEscapeFormatter(logging.Formatter):
    """Formatter that writes literal Unicode escapes as their characters."""

    def format(self, record):
        return decode_unicode_escapes(super().format(record))
