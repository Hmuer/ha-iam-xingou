"""Data update coordinator for the IAM Xingou integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    IamXingouApi,
    IamXingouAuthError,
    IamXingouConnectionError,
    IamXingouError,
    extract_properties,
)
from .const import (
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    CONF_DEVICES,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    CONF_USER_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class IamXingouCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Poll properties for all selected devices."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: IamXingouApi,
    ) -> None:
        self.api = api
        self.devices: list[dict[str, str]] = [
            {"device_id": d[CONF_DEVICE_ID], "name": d[CONF_DEVICE_NAME]}
            for d in entry.options.get(CONF_DEVICES, entry.data.get(CONF_DEVICES, []))
        ]
        interval = entry.options.get(
            CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=int(interval)),
            config_entry=entry,
        )

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        data: dict[str, dict[str, Any]] = {}
        for device in self.devices:
            device_id = device["device_id"]
            try:
                payload = await self.api.async_properties(device_id)
            except IamXingouAuthError as err:
                raise ConfigEntryAuthFailed(str(err)) from err
            except IamXingouConnectionError as err:
                raise UpdateFailed(f"connection error: {err}") from err
            except IamXingouError as err:
                raise UpdateFailed(f"API error: {err}") from err

            props = extract_properties(payload)
            _LOGGER.debug("device %s properties: %s", device_id, props)
            data[device_id] = {
                "name": device.get("name") or device_id,
                "props": props,
            }
        return data

    @property
    def token(self) -> str | None:
        return self.api.token

    @property
    def user_name(self) -> str | None:
        return self.api.user_name


def build_api(hass: HomeAssistant, entry: ConfigEntry) -> IamXingouApi:
    """Create an API client from config entry data."""
    return IamXingouApi(
        async_get_clientsession(hass),
        token=entry.data.get(CONF_TOKEN),
        user_name=entry.data.get(CONF_USER_NAME),
        user_id=entry.data.get("user_id"),
    )
