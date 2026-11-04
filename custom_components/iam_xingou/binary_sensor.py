"""Binary sensor platform for the IAM Xingou integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import IamXingouCoordinator
from .entity import CATEGORY_POWER, IamXingouEntity, classify, is_on_value, label_for


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create binary sensors for boolean properties."""
    coordinator: IamXingouCoordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = []

    for device in coordinator.devices:
        device_id = device["device_id"]
        props = coordinator.data.get(device_id, {}).get("props", {})
        for key, value in props.items():
            if not isinstance(value, bool) and classify(key) != CATEGORY_POWER:
                continue
            entities.append(IamXingouBinarySensor(coordinator, device_id, key))

    async_add_entities(entities)


class IamXingouBinarySensor(IamXingouEntity, BinarySensorEntity):
    """Boolean property."""

    def __init__(
        self, coordinator: IamXingouCoordinator, device_id: str, key: str
    ) -> None:
        super().__init__(coordinator, device_id)
        self._key = key
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{key}_binary"
        self._attr_name = label_for(key)

    @property
    def is_on(self) -> bool:
        return is_on_value(self._props.get(self._key))
