"""Shared helpers and base entities for the IAM Xingou integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    AQI_KEYS,
    CO2_KEYS,
    DOMAIN,
    FILTER_KEYS,
    HCHO_KEYS,
    HUMIDITY_KEYS,
    KEY_LABELS,
    MODE_KEYS,
    PM10_KEYS,
    PM25_KEYS,
    POWER_KEYS,
    SPEED_KEYS,
    TEMP_KEYS,
    TVOC_KEYS,
)
from .coordinator import IamXingouCoordinator

CATEGORY_POWER = "power"
CATEGORY_SPEED = "speed"
CATEGORY_MODE = "mode"
CATEGORY_PM25 = "pm25"
CATEGORY_PM10 = "pm10"
CATEGORY_TVOC = "tvoc"
CATEGORY_HCHO = "hcho"
CATEGORY_CO2 = "co2"
CATEGORY_TEMPERATURE = "temperature"
CATEGORY_HUMIDITY = "humidity"
CATEGORY_FILTER = "filterLife"
CATEGORY_AQI = "aqi"

CATEGORY_KEYS: dict[str, tuple[str, ...]] = {
    CATEGORY_POWER: POWER_KEYS,
    CATEGORY_SPEED: SPEED_KEYS,
    CATEGORY_MODE: MODE_KEYS,
    CATEGORY_PM25: PM25_KEYS,
    CATEGORY_PM10: PM10_KEYS,
    CATEGORY_TVOC: TVOC_KEYS,
    CATEGORY_HCHO: HCHO_KEYS,
    CATEGORY_CO2: CO2_KEYS,
    CATEGORY_TEMPERATURE: TEMP_KEYS,
    CATEGORY_HUMIDITY: HUMIDITY_KEYS,
    CATEGORY_FILTER: FILTER_KEYS,
    CATEGORY_AQI: AQI_KEYS,
}

CATEGORY_UNITS: dict[str, str | None] = {
    CATEGORY_PM25: "µg/m³",
    CATEGORY_PM10: "µg/m³",
    CATEGORY_TVOC: "µg/m³",
    CATEGORY_HCHO: "mg/m³",
    CATEGORY_CO2: "ppm",
    CATEGORY_TEMPERATURE: "°C",
    CATEGORY_HUMIDITY: "%",
    CATEGORY_FILTER: "%",
    CATEGORY_AQI: None,
}

CATEGORY_DEVICE_CLASS: dict[str, str | None] = {
    CATEGORY_PM25: "pm25",
    CATEGORY_PM10: "pm10",
    CATEGORY_TVOC: "volatile_organic_compounds",
    CATEGORY_CO2: "carbon_dioxide",
    CATEGORY_TEMPERATURE: "temperature",
    CATEGORY_HUMIDITY: "humidity",
    CATEGORY_AQI: "aqi",
}


def classify(key: str) -> str | None:
    """Return the semantic category of a property key."""
    for category, aliases in CATEGORY_KEYS.items():
        if key in aliases:
            return category
    lowered = key.lower()
    for category, aliases in CATEGORY_KEYS.items():
        if any(lowered == alias.lower() for alias in aliases):
            return category
    # fuzzy fallbacks
    if "pm25" in lowered or "pm2p5" in lowered:
        return CATEGORY_PM25
    if "pm10" in lowered:
        return CATEGORY_PM10
    if "tvoc" in lowered or lowered == "voc":
        return CATEGORY_TVOC
    if "hcho" in lowered or "formaldehyde" in lowered:
        return CATEGORY_HCHO
    if "co2" in lowered:
        return CATEGORY_CO2
    if "temp" in lowered:
        return CATEGORY_TEMPERATURE
    if "humi" in lowered or lowered in ("rh", "hum"):
        return CATEGORY_HUMIDITY
    if "filter" in lowered:
        return CATEGORY_FILTER
    if "aqi" in lowered:
        return CATEGORY_AQI
    if "speed" in lowered or "wind" in lowered or "gear" in lowered:
        return CATEGORY_SPEED
    if "mode" in lowered:
        return CATEGORY_MODE
    if "power" in lowered or "switch" in lowered or lowered in ("on", "onoff"):
        return CATEGORY_POWER
    return None


def label_for(key: str) -> str:
    """Human readable entity name for a property key."""
    category = classify(key)
    if category and category in KEY_LABELS:
        return KEY_LABELS[category]
    return key


def find_key(props: dict[str, Any], category: str) -> str | None:
    """Find the property key that matches a semantic category."""
    aliases = CATEGORY_KEYS.get(category, ())
    for key in props:
        if key in aliases:
            return key
    for key in props:
        if classify(key) == category:
            return key
    return None


def is_on_value(value: Any) -> bool:
    """Normalise truthy cloud values."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "on", "open", "yes")
    return False


class IamXingouEntity(CoordinatorEntity[IamXingouCoordinator]):
    """Base entity bound to one purifier."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: IamXingouCoordinator, device_id: str) -> None:
        super().__init__(coordinator)
        self._device_id = device_id

    @property
    def _device_data(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._device_id, {})

    @property
    def _props(self) -> dict[str, Any]:
        return self._device_data.get("props", {})

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=self._device_data.get("name") or self._device_id,
            manufacturer="IAM",
            model="M9 Pro (Xingou cloud)",
        )

    async def async_send_command(self, command: dict[str, Any]) -> None:
        """Send a command and refresh afterwards."""
        await self.coordinator.api.async_oper_cmd(self._device_id, command)
        await self.coordinator.async_request_refresh()
