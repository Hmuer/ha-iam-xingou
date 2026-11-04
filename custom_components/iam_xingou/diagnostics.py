"""Diagnostics support for the IAM Xingou integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_TOKEN
from .coordinator import IamXingouCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics with the token redacted."""
    coordinator: IamXingouCoordinator = entry.runtime_data
    redacted = dict(entry.data)
    if CONF_TOKEN in redacted:
        redacted[CONF_TOKEN] = "**REDACTED**"
    return {
        "entry_data": redacted,
        "options": dict(entry.options),
        "devices": coordinator.devices,
        "data": coordinator.data,
    }
