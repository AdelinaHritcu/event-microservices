"""In-memory blacklist (Lab 4 allows a dictionary/set)."""
import hashlib
from typing import Set

_JTI: Set[str] = set()      # revoked / expired tokens, by jti
_TOKENS: Set[str] = set()   # tampered tokens, by sha256 of the raw token


def _h(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def is_blacklisted(jti: str) -> bool:
    return jti in _JTI


def add(jti: str) -> None:
    if jti:
        _JTI.add(jti)


def is_token_blacklisted(token: str) -> bool:
    return _h(token) in _TOKENS


def add_token(token: str) -> None:
    if token:
        _TOKENS.add(_h(token))
