"""Charge start/stop switch entity for OK Charger."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OkChargerCoordinator, device_info_for


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: OkChargerCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.data.station is None:
        return
    async_add_entities([ChargeSwitch(coordinator), AutostartSwitch(coordinator)])


class ChargeSwitch(CoordinatorEntity[OkChargerCoordinator], SwitchEntity):
    """Toggle to start/stop a charging session."""

    _attr_has_entity_name = True
    _attr_name = "Charge"
    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator: OkChargerCoordinator) -> None:
        super().__init__(coordinator)
        station = coordinator.data.station
        assert station is not None
        self._attr_unique_id = f"{station.cs_identifier}_charge_switch"
        self._attr_device_info = device_info_for(station)

    @property
    def is_on(self) -> bool:
        station = self.coordinator.data.station
        return bool(station and station.is_charging)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_start_charge()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_stop_charge()


class AutostartSwitch(CoordinatorEntity[OkChargerCoordinator], SwitchEntity):
    """OK's autostart: the charger starts a session by itself when a car is plugged in."""

    _attr_has_entity_name = True
    _attr_name = "Autostart"
    _attr_icon = "mdi:play-circle-outline"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: OkChargerCoordinator) -> None:
        super().__init__(coordinator)
        station = coordinator.data.station
        assert station is not None
        self._attr_unique_id = f"{station.cs_identifier}_autostart"
        self._attr_device_info = device_info_for(station)

    @property
    def is_on(self) -> bool | None:
        station = self.coordinator.data.station
        return None if station is None else bool(station.auto_start)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_autostart(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_autostart(False)
