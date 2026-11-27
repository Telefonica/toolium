"""
Copyright 2016 Telefónica Investigación y Desarrollo, S.A.U.
This file is part of Toolium.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

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
