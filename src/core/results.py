from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar


ValueT = TypeVar("ValueT")
ErrorT = TypeVar("ErrorT")


@dataclass(frozen=True)
class Result(Generic[ValueT, ErrorT]):
    value: ValueT | None = None
    error: ErrorT | None = None

    @property
    def is_ok(self) -> bool:
        return self.error is None

    @classmethod
    def ok(cls, value: ValueT) -> "Result[ValueT, ErrorT]":
        return cls(value=value)

    @classmethod
    def fail(cls, error: ErrorT) -> "Result[ValueT, ErrorT]":
        return cls(error=error)
