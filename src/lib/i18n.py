"""Internationalization scaffolding (T053).

Simple placeholder providing locale negotiation and message lookup hooks. Real
implementations would integrate Babel or similar. This keeps surface minimal
until multi-locale requirements materialize.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

_DEFAULT_LOCALE = "en"


@dataclass
class LocaleContext:
    locale: str


class I18n:
    def __init__(self, messages: Mapping[str, Mapping[str, str]] | None = None) -> None:
        # messages: {locale: {key: string}}
        self._messages = messages or {_DEFAULT_LOCALE: {}}

    def negotiate(self, accept_language: str | None) -> str:
        if not accept_language:
            return _DEFAULT_LOCALE
        # extremely naive: take first token before comma
        primary = accept_language.split(",")[0].strip().lower()
        return primary if primary in self._messages else _DEFAULT_LOCALE

    def gettext(self, key: str, locale: str | None = None) -> str:
        loc = locale or _DEFAULT_LOCALE
        return self._messages.get(loc, {}).get(key, self._messages[_DEFAULT_LOCALE].get(key, key))


__all__ = ["I18n", "LocaleContext"]
