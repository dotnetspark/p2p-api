from __future__ import annotations

from dataclasses import asdict, is_dataclass
from decimal import Decimal
import hashlib
import json


def build_idempotency_fingerprint(operation: str, payload: object) -> str:
    normalized_payload = _normalize_value(payload)
    encoded_payload = json.dumps(
        {"operation": operation, "payload": normalized_payload},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(encoded_payload.encode("ascii")).hexdigest()


def _normalize_value(value: object) -> object:
    if is_dataclass(value):
        return _normalize_value(asdict(value))
    if isinstance(value, Decimal):
        return format(value.quantize(Decimal("0.01")), "f")
    if isinstance(value, dict):
        return {str(key): _normalize_value(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize_value(item) for item in value]
    return value