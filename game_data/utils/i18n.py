# path: game_data/utils/i18n.py

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Mapping, Optional, Union
import json

from utils.logger import get_logger

log = get_logger(name=__name__, context="I18N")

@dataclass
class _I18nState:
    locales_dir: Path
    current_lang: str
    default_lang: str
    loaded: Dict[str, Mapping[str, Any]]
    cache: Dict[tuple[str, str], str]
    lock: RLock

_I18N: Optional[_I18nState] = None

class I18nNotInitializedError(RuntimeError):
    """init_i18n() must be called before usage."""

class I18nKeyError(KeyError):
    """Raised when a translation key is missing in both primary and fallback."""

def init_i18n(lang: str, locales_dir: Union[str, Path], default_lang: str = "en") -> None:
    global _I18N
    _I18N = _I18nState(
        locales_dir=Path(locales_dir),
        current_lang=lang,
        default_lang=default_lang,
        loaded={},
        cache={},
        lock=RLock(),
    )
    _load_locale(lang)
    if default_lang != lang:
        _load_locale(default_lang)

def set_lang(lang: str) -> None:
    s = _require_i18n()
    with s.lock:
        s.current_lang = lang
        _load_locale(lang)

def get_loc(key: Optional[str], vars: Optional[Mapping[str, Any]] = None, default: Optional[str] = None) -> str:
    if not key:
        if default is not None:
            return default
        raise I18nKeyError("Missing i18n key argument.")
    s = _require_i18n()
    with s.lock:
        ck = (s.current_lang, key)
        if ck in s.cache:
            return _safe_format(s.cache[ck], vars)
        primary = _load_locale(s.current_lang)
        fallback = _load_locale(s.default_lang) if s.default_lang != s.current_lang else primary
        text = _lookup(primary, key) or _lookup(fallback, key)
        if text is None:
            if default is not None:
                return _safe_format(default, vars)
            raise I18nKeyError(f"Missing i18n key '{key}' for '{s.current_lang}' (fallback '{s.default_lang}').")
        s.cache[ck] = text
        return _safe_format(text, vars)

def _require_i18n() -> _I18nState:
    if _I18N is None:
        raise I18nNotInitializedError("Call init_i18n(lang, locales_dir) before using get_loc().")
    return _I18N

def _load_locale(lang: str) -> Mapping[str, Any]:
    s = _require_i18n()
    if lang in s.loaded:
        return s.loaded[lang]
    path = s.locales_dir / f"{lang}.json"
    if not path.exists():
        s.loaded[lang] = {}
        return s.loaded[lang]
    with path.open("r", encoding="utf-8") as f:
        s.loaded[lang] = json.load(f)
    return s.loaded[lang]

def _lookup(tree: Mapping[str, Any], dotted: str) -> Optional[str]:
    node: Any = tree
    for part in dotted.split("."):
        if not isinstance(node, Mapping) or part not in node:
            return None
        node = node[part]
    return node if isinstance(node, str) else None

def _safe_format(text: str, vars: Optional[Mapping[str, Any]]) -> str:
    if not vars:
        return text
    try:
        return text.format(**vars)  # Pourquoi: lisible côté contenu.
    except Exception:
        return text  # Pourquoi: ne pas crasher si une var manque.

