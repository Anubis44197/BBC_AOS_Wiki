"""Retry helper for transient BBC-AOS loop failures."""

import time
from typing import Callable, Iterable, Tuple, Type, TypeVar

T = TypeVar("T")


class RetryEngine:
    """Retries transient operations with 1s, 2s, 4s backoff by default."""

    def __init__(self, delays: Iterable[float] = (1.0, 2.0, 4.0)) -> None:
        self.delays = list(delays)

    def run(
        self,
        operation: Callable[[], T],
        transient_errors: Tuple[Type[BaseException], ...] = (OSError, TimeoutError),
    ) -> T:
        last_error: BaseException | None = None
        for attempt in range(len(self.delays) + 1):
            try:
                return operation()
            except transient_errors as exc:
                last_error = exc
                if attempt >= len(self.delays):
                    break
                time.sleep(self.delays[attempt])
        if last_error is not None:
            raise last_error
        raise RuntimeError("Retry operation failed without capturing an exception")
