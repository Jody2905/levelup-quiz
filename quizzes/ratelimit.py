"""Small fixed-window rate limiter built on Django's cache (no extra packages).

Uses the default cache. The built-in local-memory cache works for one server
process; in production with several workers, point CACHES at Redis or
Memcached so every worker shares the same counters.
"""

import hashlib

from django.conf import settings
from django.core.cache import cache


def client_ip(request):
    # REMOTE_ADDR only. X-Forwarded-For can be forged unless a trusted proxy sets it.
    return request.META.get("REMOTE_ADDR", "unknown")


def _key(scope, *parts):
    raw = "|".join(str(p).lower() for p in parts)
    return f"rl:{scope}:{hashlib.sha256(raw.encode()).hexdigest()[:32]}"


def count(scope, *parts):
    return cache.get(_key(scope, *parts), 0)


def increment(scope, *parts, window):
    key = _key(scope, *parts)
    # add() only sets the key if it doesn't exist, which starts the window
    if cache.add(key, 1, timeout=window):
        return 1
    try:
        return cache.incr(key)
    except ValueError:  # key expired between add() and incr()
        cache.set(key, 1, timeout=window)
        return 1


def reset(scope, *parts):
    cache.delete(_key(scope, *parts))


def limit(name):
    """Return (max_attempts, window_seconds) for a named limit from settings."""
    return settings.RATE_LIMITS[name]


def is_limited(scope, *parts):
    max_attempts, _ = limit(scope)
    return count(scope, *parts) >= max_attempts


def hit(scope, *parts):
    """Record one attempt. Returns True if the caller is now over the limit."""
    max_attempts, window = limit(scope)
    return increment(scope, *parts, window=window) > max_attempts
