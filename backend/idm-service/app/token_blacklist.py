from typing import Set

_BLACKLIST: Set[str] = set()

def is_blacklisted(jti: str) -> bool:
    return jti in _BLACKLIST

def add(jti: str) -> None:
    if jti:
        _BLACKLIST.add(jti)
