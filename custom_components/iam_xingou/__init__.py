"""Set up the IAM Xingou integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv

from .api import IamXingouAuthError, IamXingouConnectionError, IamXingouError
from .const import (
    CONF_DEVICE_ID,
    CONF_DEVICES,
    CONF_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import IamXingouCoordinator, build_api

_LOGGER = logging.getLogger(__name__)

type IamXingouConfigEntry = ConfigEntry[IamXingouCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: IamXingouConfigEntry) -> bool:
    """Set up one account."""
    api = build_api(hass, entry)
    coordinator = IamXingouCoordinator(hass, entry, api)

    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        raise
    except IamXingouConnectionError as err:
        raise ConfigEntryNotReady(str(err)) from err

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: IamXingouConfigEntry) -> bool:
    """Unload one account."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(
    hass: HomeAssistant, entry: IamXingouConfigEntry
) -> None:
    """Reload the entry after options changed."""
    await hass.config_entries.async_reload(entry.entry_id)


def _async_register_services(hass: HomeAssistant) -> None:
    """Register the generic command service (once)."""
    if hass.services.has_service(DOMAIN, "oper_cmd"):
        return

    async def async_oper_cmd(call: ServiceCall) -> None:
        device_id: str = call.data["device_id"]
        command: dict[str, Any] = call.data["command"]
        entry: IamXingouConfigEntry | None = None
        for candidate in hass.config_entries.async_entries(DOMAIN):
            coordinator: IamXingouCoordinator = candidate.runtime_data
            if any(d["device_id"] == device_id for d in coordinator.devices):
                entry = candidate
                break
        if entry is None:
            raise IamXingouError(f"unknown device_id: {device_id}")
        coordinator = entry.runtime_data
        try:
            await coordinator.api.async_oper_cmd(device_id, command)
        except IamXingouAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        "oper_cmd",
        async_oper_cmd,
        schema=vol.Schema(
            {
                vol.Required("device_id"): cv.string,
                vol.Required("command"): dict,
            }
        ),
    )
