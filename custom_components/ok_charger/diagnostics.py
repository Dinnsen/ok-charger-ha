"""Diagnostics for OK Charger: OK's raw answers, with secrets hidden."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import raw
from .const import DOMAIN
from .coordinator import OkChargerCoordinator


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    coordinator: OkChargerCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data
    station = data.station
    return {
        "entry": raw.redact(dict(entry.data)),
        "station": None
        if station is None
        else {
            "model": station.model,
            "vendor": station.vendor,
            "firmware": station.firmware_version,
            "connector_id": station.connector_id,
            "connector_power_kw": station.connector_power_kw,
            "auto_start": station.auto_start,
            "is_charging": station.is_charging,
        },
        "locations": raw.redact(data.raw_stations),
        "current_chargings": raw.redact(data.raw_active),
        "last_session": raw.redact(data.last_session),
        "last_session_ended": data.last_session_ended.isoformat() if data.last_session_ended else None,
        "last_receipt": raw.redact(data.last_receipt),
        "prices_sample": data.prices[:3]
        and [
            {"applicable_time": p.applicable_time.isoformat(), "total_ore_per_kwh": p.total_ore_per_kwh}
            for p in data.prices[:3]
        ],
    }
