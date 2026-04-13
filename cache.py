import time

_cache = {}

def get(key):
    entry = _cache.get(key)
    if entry and time.time() < entry["expires"]:
        return entry["value"]
    return None

def set(key, value, ttl=300):
    _cache[key] = {"value": value, "expires": time.time() + ttl}