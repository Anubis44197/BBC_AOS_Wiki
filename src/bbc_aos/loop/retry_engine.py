"""Retry helper for transient BBC-AOS loop failures."""

import time
from typing import Callable, Iterable, Tuple, TypeVar

T = TypeVar("T")


class RetryEngine:
    """Retries transient operations with 1s, 2s, 4s backoff by default."""

    def __init__(self, delays: Iterable[float] = (1.0, 2.0, 4.0)) -> None:
        self.delays = list(delays)

    def run(self, operation: Callable[[], T], transient_errors: Tuple[type, ...] = (OSError, TimeoutError)) -> T:
        last_error = None
        for attempt in range(len(self.delays) + 1):
            try:
                return operation()
            except transient_errors as exc:
                last_error = exc
                if attempt >= len(self.delays):
                    break
                time.sleep(self.delays[attempt])
        raise last_error  # type: ignore[misc]
