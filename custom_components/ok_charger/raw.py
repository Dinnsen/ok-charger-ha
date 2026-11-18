"""Reading OK's raw answers without knowing every field in advance.

OK's API is not documented. These helpers pull the few things the entities
need out of whatever the backend sends (a start time, a status, an energy
figure), keep the rest as attributes, and hide what must not leave Home
Assistant. They import nothing from Home Assistant, so they are easy to test.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

# Keys never shown as attributes or in diagnostics (matched case-insensitively,
# as a whole key or as part of one).
SECRET_PARTS = (
    "token",
    "password",
    "kodeord",
    "email",
    "adresse",
    "address",
    "street",
    "zip",
    "postal",
    "city",
    "locationname",
    "phone",
    "telefon",
    "latitude",
    "longitude",
    "deviceid",
    "friendlydeviceid",
    "appid",
    "brugernr",
    "customer",
    "kunde",
)

START_KEYS = ("startTime", "startedAt", "startDate", "start", "sessionStart", "chargingStart", "created", "createdAt")
END_KEYS = ("endTime", "endedAt", "endDate", "end", "sessionEnd", "chargingEnd", "stoppedAt", "stopTime")
STATUS_KEYS = ("status", "state", "connectorStatus", "chargingStatus")
ENERGY_KEYS = (
    "kwh",
    "kWh",
    "energy",
    "energyKwh",
    "totalKwh",
    "totalEnergy",
    "consumption",
    "consumedKwh",
    "meterValue",
)
COST_KEYS = ("price", "totalPrice", "amount", "totalAmount", "cost", "totalCost")


def is_secret(key: str) -> bool:
    low = key.lower().replace("_", "").replace("-", "")
    return any(part in low for part in SECRET_PARTS)


def redact(value: Any) -> Any:
    """A copy with every secret key's value replaced."""
    if isinstance(value, dict):
        return {k: ("**redacted**" if is_secret(str(k)) else redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def flatten(value: Any, prefix: str = "", depth: int = 3) -> dict[str, Any]:
    """Nested dicts as flat ``a_b_c`` attributes, secrets left out; lists of plain values kept, others counted."""
    out: dict[str, Any] = {}
    if not isinstance(value, dict):
        return out
    for key, item in value.items():
        if is_secret(str(key)):
            continue
        name = f"{prefix}{key}"
        if isinstance(item, dict) and depth > 0:
            out.update(flatten(item, f"{name}_", depth - 1))
        elif isinstance(item, list):
            if all(not isinstance(x, (dict, list)) for x in item):
                out[name] = item
            else:
                out[f"{name}_count"] = len(item)
        else:
            out[name] = item
    return out


def _find(value: Any, keys: tuple[str, ...], depth: int = 2) -> Any:
    """The first of the keys found in the dict or, failing that, in the dicts inside it."""
    if not isinstance(value, dict):
        return None
    lowered = {str(k).lower(): v for k, v in value.items()}
    for key in keys:
        if key.lower() in lowered and lowered[key.lower()] not in (None, ""):
            return lowered[key.lower()]
    if depth > 0:
        for item in value.values():
            if isinstance(item, dict) and (found := _find(item, keys, depth - 1)) is not None:
                return found
    return None


def parse_time(value: Any) -> dt.datetime | None:
    """An ISO time or an epoch in seconds or milliseconds, as an aware datetime."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        seconds = value / 1000 if value > 1e11 else value
        try:
            return dt.datetime.fromtimestamp(seconds, tz=dt.timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        text = value.strip().replace("Z", "+00:00")
        try:
            parsed = dt.datetime.fromisoformat(text)
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)
    return None


def parse_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return None
    return None


def started(entry: Any) -> dt.datetime | None:
    return parse_time(_find(entry, START_KEYS))


def ended(entry: Any) -> dt.datetime | None:
    return parse_time(_find(entry, END_KEYS))


def status(entry: Any) -> str | None:
    found = _find(entry, STATUS_KEYS)
    return str(found) if found is not None and not isinstance(found, (dict, list)) else None


def energy(entry: Any) -> float | None:
    return parse_number(_find(entry, ENERGY_KEYS))


def cost(entry: Any) -> float | None:
    return parse_number(_find(entry, COST_KEYS))
