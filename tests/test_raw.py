"""Reading OK's raw answers: times, numbers, statuses and secrets."""

from __future__ import annotations

import datetime as dt
import importlib.util
import pathlib

_PATH = pathlib.Path(__file__).parent.parent / "custom_components" / "ok_charger" / "raw.py"
_spec = importlib.util.spec_from_file_location("ok_raw", _PATH)
raw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(raw)


def test_secrets_are_hidden_at_any_depth() -> None:
    data = {
        "email": "a@b.dk",
        "app_id": "x",
        "chargingToken": "t",
        "location": {"streetAddress": "Vej 1", "name": "Hjem"},
        "list": [{"deviceId": "d", "kwh": 3}],
        "receipt": {"locationName": "Vej 1", "chargingStationName": "Min OK", "locationId": "u"},
    }
    out = raw.redact(data)
    assert out["email"] == out["app_id"] == out["chargingToken"] == "**redacted**"
    assert out["location"]["streetAddress"] == "**redacted**"
    assert out["location"]["name"] == "Hjem"
    assert out["list"][0] == {"deviceId": "**redacted**", "kwh": 3}
    assert out["receipt"] == {"locationName": "**redacted**", "chargingStationName": "Min OK", "locationId": "u"}


def test_flatten_leaves_secrets_out_and_counts_lists_of_dicts() -> None:
    flat = raw.flatten({"a": {"b": 1, "token": "t"}, "c": [1, 2], "d": [{"x": 1}], "email": "e"})
    assert flat == {"a_b": 1, "c": [1, 2], "d_count": 1}


def test_times_from_iso_or_epoch() -> None:
    assert raw.parse_time("2026-11-18T01:00:00Z") == dt.datetime(2026, 11, 18, 1, tzinfo=dt.timezone.utc)
    assert raw.parse_time("2026-11-18T02:00:00") == dt.datetime(2026, 11, 18, 2, tzinfo=dt.timezone.utc)
    assert raw.parse_time(1794963600000) == raw.parse_time(1794963600)
    assert raw.parse_time("soon") is None
    assert raw.parse_time(True) is None


def test_fields_are_found_by_any_known_name_and_nested_once() -> None:
    session = {"chargingStart": "2026-11-18T00:01:00+01:00", "meter": {"totalKwh": "25,3"}, "Status": "Charging"}
    assert raw.started(session) == dt.datetime(2026, 11, 18, 0, 1, tzinfo=dt.timezone(dt.timedelta(hours=1)))
    assert raw.energy(session) == 25.3
    assert raw.status(session) == "Charging"
    assert raw.ended(session) is None
    assert raw.cost({"totalPrice": 33.03}) == 33.03
    assert raw.status({"state": {"x": 1}}) is None
