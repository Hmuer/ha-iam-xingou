"""Fan platform (power + wind speed) for the IAM Xingou integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import IamXingouCoordinator
from .entity import (
    CATEGORY_MODE,
    CATEGORY_POWER,
    CATEGORY_SPEED,
    IamXingouEntity,
    find_key,
    is_on_value,
)

# Number of discrete speed levels assumed for the percentage mapping.
SPEED_RANGE = (1, 5)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one fan entity per purifier."""
    coordinator: IamXingouCoordinator = entry.runtime_data
    entities: list[FanEntity] = []

    for device in coordinator.devices:
        device_id = device["device_id"]
        props = coordinator.data.get(device_id, {}).get("props", {})
        if not find_key(props, CATEGORY_POWER) and not find_key(props, CATEGORY_SPEED):
            continue
        entities.append(IamXingouPurifierFan(coordinator, device_id))

    async_add_entities(entities)


class IamXingouPurifierFan(IamXingouEntity, FanEntity):
    """Air purifier exposed as a fan entity."""

    _attr_name = None
    _attr_speed_count = SPEED_RANGE[1]

    def __init__(self, coordinator: IamXingouCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{DOMAIN}_{device_id}_fan"

    # ------------------------------------------------------------- attributes
    @property
    def _power_key(self) -> str | None:
        return find_key(self._props, CATEGORY_POWER)

    @property
    def _speed_key(self) -> str | None:
        return find_key(self._props, CATEGORY_SPEED)

    @property
    def _mode_key(self) -> str | None:
        return find_key(self._props, CATEGORY_MODE)

    @property
    def supported_features(self) -> FanEntityFeature:
        features = FanEntityFeature(0)
        if self._power_key or self._speed_key:
            features |= FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        if self._speed_key:
            features |= FanEntityFeature.SET_SPEED
        if self._mode_key:
            features |= FanEntityFeature.PRESET_MODE
        return features

    @property
    def is_on(self) -> bool:
        power_key = self._power_key
        if power_key:
            return is_on_value(self._props.get(power_key))
        speed_key = self._speed_key
        if speed_key:
            value = self._props.get(speed_key)
            return isinstance(value, (int, float)) and value > 0
        return False

    def _speed_value(self) -> int | None:
        speed_key = self._speed_key
        if not speed_key:
            return None
        value = self._props.get(speed_key)
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            try:
                return int(float(value))
            except ValueError:
                return None
        return None

    @property
    def percentage(self) -> int | None:
        value = self._speed_value()
        if value is None:
            return None
        return min(100, max(0, int(round(value * 100 / SPEED_RANGE[1]))))

    @property
    def preset_modes(self) -> list[str] | None:
        mode_key = self._mode_key
        if not mode_key:
            return None
        current = self._props.get(mode_key)
        modes = ["auto", "sleep", "manual", "strong", "silent"]
        if isinstance(current, str) and current not in modes:
            modes.append(current)
        return modes

    @property
    def preset_mode(self) -> str | None:
        mode_key = self._mode_key
        if not mode_key:
            return None
        value = self._props.get(mode_key)
        return str(value) if isinstance(value, str) else None

    # --------------------------------------------------------------- commands
    async def async_turn_on(
        self, percentage: int | None = None, preset_mode: str | None = None, **kwargs: Any
    ) -> None:
        power_key = self._power_key
        if power_key:
            await self.async_send_command({power_key: 1})
        if percentage is not None:
            await self.async_set_percentage(percentage)
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)

    async def async_turn_off(self, **kwargs: Any) -> None:
        power_key = self._power_key
        speed_key = self._speed_key
        command: dict[str, Any] = {}
        if power_key:
            command[power_key] = 0
        if not command and speed_key:
            command[speed_key] = 0
        if command:
            await self.async_send_command(command)

    async def async_set_percentage(self, percentage: int) -> None:
        speed_key = self._speed_key
        if not speed_key:
            return
        if percentage == 0:
            await self.async_turn_off()
            return
        level = max(
            SPEED_RANGE[0],
            min(SPEED_RANGE[1], round(percentage * SPEED_RANGE[1] / 100)),
        )
        await self.async_send_command({speed_key: int(level)})

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        mode_key = self._mode_key
        if not mode_key:
            return
        await self.async_send_command({mode_key: preset_mode})
