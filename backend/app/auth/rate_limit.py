"""
Tiny in-memory limiter for failed login / registration attempts.
Per-process only: enough for a single uvicorn worker. For several workers or
servers, replace it with Redis or a gateway-level rate limit.
"""
import time                                                                       # gives us a clock to measure when each failure happened
from collections import defaultdict                                               # dict that auto-creates an empty list for new keys

from fastapi import HTTPException, status                                         # used to return a 429 error to the client

MAX_FAILURES = 5                                                                  # how many failed attempts are allowed inside the window
WINDOW_SECONDS = 15 * 60                                                          # window length: 15 minutes expressed in seconds

_failures = defaultdict(list)                                                     # key -> list of failure timestamps (the in-memory store)


def _recent(key: str):                                                            # returns only the failures that are still inside the window
    """
    WHY WE USE THIS FUNCTION:
    - Old failures should stop counting after 15 minutes, so we drop them
      every time we look at a key.
    - Cleaning on access means no background job is needed.
    - The leading underscore means it is a private helper for this file only.
    """
    now = time.monotonic()                                                        # current time from a clock that never jumps backwards
    _failures[key] = [t for t in _failures[key] if now - t < WINDOW_SECONDS]      # keep only timestamps younger than the window
    return _failures[key]                                                         # the cleaned list for this key


def check(key: str) -> None:                                                      # blocks the request if the key has too many failures
    """
    WHY WE USE THIS FUNCTION:
    - Called BEFORE doing the real work (login/register) to stop brute-force
      guessing of passwords or the invite code.
    - Raises 429 Too Many Requests with a Retry-After header, so clients and
      browsers know how many seconds to wait.
    - Does nothing when the key is under the limit.
    """
    recent = _recent(key)                                                         # failures for this key in the last 15 minutes
    if len(recent) >= MAX_FAILURES:                                               # limit reached
        retry_after = int(WINDOW_SECONDS - (time.monotonic() - recent[0])) + 1    # seconds until the oldest failure expires (+1 to round up)
        raise HTTPException(                                                      # stop the request with an error
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,                        # 429 = too many requests
            detail="Too many failed attempts. Please try again later.",           # message shown to the client
            headers={"Retry-After": str(retry_after)},                            # standard header telling when to retry
        )


def fail(key: str) -> None:                                                       # records one failed attempt for the key
    """
    WHY WE USE THIS FUNCTION:
    - Called when a login or invite code check fails, so repeated failures
      add up until check() starts blocking.
    - Only failures are counted, so normal successful users are never slowed down.
    """
    _recent(key).append(time.monotonic())                                         # clean old entries, then add the current time


def reset(key: str) -> None:                                                      # clears all failures for the key
    """
    WHY WE USE THIS FUNCTION:
    - Called after a successful login so a real admin who mistyped a few
      times starts fresh and is not locked out later.
    - pop(key, None) is safe even if the key does not exist (no KeyError).
    """
    _failures.pop(key, None)                                                      # remove the key's list; ignore if it is missing


def clear_all() -> None:  # used by tests
    """
    WHY WE USE THIS FUNCTION:
    - Wipes every key at once so each automated test starts with a clean
      limiter and tests do not affect one another.
    - Not used by the app itself.
    """
    _failures.clear()                                                             # empty the whole store