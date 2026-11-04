"""Sensor platform for the IAM Xingou integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import IamXingouCoordinator
from .entity import (
    CATEGORY_AQI,
    CATEGORY_CO2,
    CATEGORY_FILTER,
    CATEGORY_HCHO,
    CATEGORY_HUMIDITY,
    CATEGORY_PM10,
    CATEGORY_PM25,
    CATEGORY_POWER,
    CATEGORY_SPEED,
    CATEGORY_TEMPERATURE,
    CATEGORY_TVOC,
    IamXingouEntity,
    classify,
    label_for,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create sensors for every numeric (or text) property."""
    coordinator: IamXingouCoordinator = entry.runtime_data
    entities: list[SensorEntity] = []

    for device in coordinator.devices:
        device_id = device["device_id"]
        props = coordinator.data.get(device_id, {}).get("props", {})
        for key, value in props.items():
            category = classify(key)
            if category in (CATEGORY_POWER, CATEGORY_SPEED):
                continue
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                entities.append(IamXingouSensor(coordinator, device_id, key, category))
            elif isinstance(value, str):
                entities.append(IamXingouTextSensor(coordinator, device_id, key))

    async_add_entities(entities)


def _unit_for(category: str | None, value: Any) -> str | None:
    if category == CATEGORY_TEMPERATURE:
        return UnitOfTemperature.CELSIUS
    if category == CATEGORY_HUMIDITY:
        return PERCENTAGE
    if category == CATEGORY_FILTER:
        return PERCENTAGE
    if category in (CATEGORY_PM25, CATEGORY_PM10, CATEGORY_TVOC):
        return "µg/m³"
    if category == CATEGORY_HCHO:
        return "mg/m³"
    if category == CATEGORY_CO2:
        return "ppm"
    return None


def _device_class_for(category: str | None) -> SensorDeviceClass | None:
    mapping = {
        CATEGORY_PM25: SensorDeviceClass.PM25,
        CATEGORY_PM10: SensorDeviceClass.PM10,
        CATEGORY_TVOC: SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
        CATEGORY_CO2: SensorDeviceClass.CO2,
        CATEGORY_TEMPERATURE: SensorDeviceClass.TEMPERATURE,
        CATEGORY_HUMIDITY: SensorDeviceClass.HUMIDITY,
        CATEGORY_AQI: SensorDeviceClass.AQI,
    }
    return mapping.get(category)


class IamXingouSensor(IamXingouEntity, SensorEntity):
    """Numeric property sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: IamXingouCoordinator,
        device_id: str,
        key: str,
        category: str | None,
    ) -> None:
        super().__init__(coordinator, device_id)
        self._key = key
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{key}"
        self._attr_name = label_for(key)
        self._attr_native_unit_of_measurement = _unit_for(category, None)
        self._attr_device_class = _device_class_for(category)

    @property
    def native_value(self) -> float | int | None:
        value = self._props.get(self._key)
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None
        return None


class IamXingouTextSensor(IamXingouEntity, SensorEntity):
    """Text property sensor (mode names, fault codes, ...)."""

    def __init__(
        self, coordinator: IamXingouCoordinator, device_id: str, key: str
    ) -> None:
        super().__init__(coordinator, device_id)
        self._key = key
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{key}_text"
        self._attr_name = label_for(key)

    @property
    def native_value(self) -> str | None:
        value = self._props.get(self._key)
        if value is None:
            return None
        return str(value)
