"""Select platform (working mode) for the IAM Xingou integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import IamXingouCoordinator
from .entity import CATEGORY_MODE, IamXingouEntity, find_key, label_for

# Common Xingou purifier modes; the current cloud value is always added as well.
GUESSED_MODES = ("auto", "manual", "sleep", "strong", "silent", "smart")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one select entity per device that reports a textual mode."""
    coordinator: IamXingouCoordinator = entry.runtime_data
    entities: list[SelectEntity] = []

    for device in coordinator.devices:
        device_id = device["device_id"]
        props = coordinator.data.get(device_id, {}).get("props", {})
        mode_key = find_key(props, CATEGORY_MODE)
        if not mode_key:
            continue
        current = props.get(mode_key)
        if not isinstance(current, str):
            continue
        entities.append(IamXingouModeSelect(coordinator, device_id, mode_key))

    async_add_entities(entities)


class IamXingouModeSelect(IamXingouEntity, SelectEntity):
    """Working mode of the purifier."""

    def __init__(
        self, coordinator: IamXingouCoordinator, device_id: str, key: str
    ) -> None:
        super().__init__(coordinator, device_id)
        self._key = key
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{key}_select"
        self._attr_name = label_for(key)

    def _options(self) -> list[str]:
        current = self._props.get(self._key)
        options = [m for m in GUESSED_MODES]
        if isinstance(current, str) and current not in options:
            options.append(current)
        return options

    @property
    def options(self) -> list[str]:
        return self._options()

    @property
    def current_option(self) -> str | None:
        value: Any = self._props.get(self._key)
        return str(value) if isinstance(value, str) else None

    async def async_select_option(self, option: str) -> None:
        await self.async_send_command({self._key: option})
