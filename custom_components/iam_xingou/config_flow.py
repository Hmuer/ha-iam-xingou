"""Config flow for the IAM Xingou integration."""

from __future__ import annotations

import json
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    IamXingouApi,
    IamXingouAuthError,
    IamXingouConnectionError,
    IamXingouError,
    IamXingouRateLimitError,
    extract_devices,
)
from .const import (
    CONF_CODE,
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    CONF_DEVICES,
    CONF_KEY_MAP,
    CONF_PHONE,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    CONF_USER_ID,
    CONF_USER_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class IamXingouConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the phone + SMS login flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._phone: str = ""
        self._api: IamXingouApi | None = None
        self._devices: list[dict[str, str]] = []
        self._sms_warning: bool = False

    # ------------------------------------------------------------ user steps
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose between the SMS login and a manual token import."""
        return self.async_show_menu(step_id="user", menu_options=["phone", "token"])

    async def async_step_phone(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            phone = user_input[CONF_PHONE].strip()
            api = IamXingouApi(async_get_clientsession(self.hass))
            try:
                await api.async_send_code(phone)
            except IamXingouRateLimitError:
                # Too many requests: still allow the user to enter a code that
                # was requested from the official app (same cloud backend).
                self._phone = phone
                self._api = api
                return await self.async_step_sms()
            except IamXingouError as err:
                # The cloud sometimes answers with an error code while still
                # delivering the SMS. Never block the flow on this: let the
                # user type the code (or request it from the official app).
                _LOGGER.warning("send code failed, continuing anyway: %s", err)
                self._phone = phone
                self._api = api
                self._sms_warning = True
                return await self.async_step_sms()
            else:
                self._phone = phone
                self._api = api
                return await self.async_step_sms()

        return self.async_show_form(
            step_id="phone",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PHONE): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.TEL)
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_token(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Import an existing access token (useful while SMS is rate limited)."""
        errors: dict[str, str] = {}
        if user_input is not None:
            token = user_input[CONF_TOKEN].strip()
            user_name = user_input[CONF_USER_NAME].strip()
            user_id = (user_input.get("user_id") or "").strip()
            api = IamXingouApi(
                async_get_clientsession(self.hass),
                token=token,
                user_name=user_name,
                user_id=user_id,
            )
            try:
                home = await api.async_homepage()
            except IamXingouAuthError:
                errors["base"] = "invalid_token"
            except IamXingouError as err:
                _LOGGER.warning("token import failed: %s", err)
                errors["base"] = "unknown"
            else:
                self._devices = extract_devices(home)
                if not self._devices:
                    errors["base"] = "no_devices"
                else:
                    self._api = api
                    self._phone = user_name
                    await self.async_set_unique_id(user_name)
                    return await self.async_step_devices()

        return self.async_show_form(
            step_id="token",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TOKEN): TextSelector(),
                    vol.Required(CONF_USER_NAME): TextSelector(),
                    vol.Optional("user_id"): TextSelector(),
                }
            ),
            errors=errors,
        )

    async def async_step_sms(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None and self._api is not None:
            try:
                await self._api.async_login(self._phone, user_input[CONF_CODE].strip())
                home = await self._api.async_homepage()
            except IamXingouAuthError:
                errors["base"] = "invalid_code"
            except IamXingouConnectionError:
                errors["base"] = "cannot_connect"
            except IamXingouError as err:
                _LOGGER.warning("login failed: %s", err)
                errors["base"] = "unknown"
            else:
                self._devices = extract_devices(home)
                if not self._devices:
                    errors["base"] = "no_devices"
                else:
                    await self.async_set_unique_id(self._api.user_name or self._phone)
                    return await self.async_step_devices()

        if self._sms_warning and not errors:
            errors["base"] = "sms_maybe_failed"

        return self.async_show_form(
            step_id="sms",
            description_placeholders={"phone": self._phone},
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CODE): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.NUMBER)
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            selected = set(user_input[CONF_DEVICES])
            devices = [
                {
                    CONF_DEVICE_ID: d["device_id"],
                    CONF_DEVICE_NAME: d["name"],
                    "model": d.get("model", ""),
                }
                for d in self._devices
                if d["device_id"] in selected
            ]
            assert self._api is not None
            return self.async_create_entry(
                title=self._api.user_name or self._phone,
                data={
                    CONF_PHONE: self._phone,
                    CONF_TOKEN: self._api.token,
                    CONF_USER_NAME: self._api.user_name,
                    CONF_USER_ID: self._api.user_id,
                    CONF_DEVICES: devices,
                    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                },
            )

        options = [
            SelectOptionDict(value=d["device_id"], label=f"{d['name']} ({d['model'] or d['device_id']})")
            for d in self._devices
        ]
        return self.async_show_form(
            step_id="devices",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICES): SelectSelector(
                        SelectSelectorConfig(
                            options=options,
                            multiple=True,
                            mode=SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
        )

    # ---------------------------------------------------------------- reauth
    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        self._phone = entry_data.get(CONF_PHONE, "")
        return await self.async_step_reauth_user()

    async def async_step_reauth_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            phone = user_input[CONF_PHONE].strip()
            api = IamXingouApi(async_get_clientsession(self.hass))
            try:
                await api.async_send_code(phone)
            except IamXingouRateLimitError:
                self._phone = phone
                self._api = api
                return await self.async_step_reauth_sms()
            except IamXingouError:
                errors["base"] = "sms_failed"
            else:
                self._phone = phone
                self._api = api
                return await self.async_step_reauth_sms()

        return self.async_show_form(
            step_id="reauth_user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PHONE, default=self._phone): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.TEL)
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_reauth_sms(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if user_input is not None and self._api is not None and entry is not None:
            try:
                await self._api.async_login(self._phone, user_input[CONF_CODE].strip())
            except IamXingouAuthError:
                errors["base"] = "invalid_code"
            except IamXingouError:
                errors["base"] = "unknown"
            else:
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={
                        **entry.data,
                        CONF_PHONE: self._phone,
                        CONF_TOKEN: self._api.token,
                        CONF_USER_NAME: self._api.user_name,
                        CONF_USER_ID: self._api.user_id,
                    },
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_sms",
            description_placeholders={"phone": self._phone},
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CODE): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.NUMBER)
                    )
                }
            ),
            errors=errors,
        )

    # --------------------------------------------------------------- options
    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        return IamXingouOptionsFlow()


class IamXingouOptionsFlow(OptionsFlow):
    """Options: polling interval and optional property key overrides."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            key_map_raw = (user_input.get(CONF_KEY_MAP) or "").strip()
            if key_map_raw:
                try:
                    key_map = json.loads(key_map_raw)
                except json.JSONDecodeError:
                    errors["base"] = "invalid_json"
                else:
                    if not isinstance(key_map, dict):
                        errors["base"] = "invalid_json"
            if not errors:
                options = {
                    CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
                    CONF_KEY_MAP: (user_input.get(CONF_KEY_MAP) or "").strip(),
                }
                return self.async_create_entry(data=options)

        current = self.config_entry.options
        key_map = current.get(CONF_KEY_MAP, "")
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            max=MAX_SCAN_INTERVAL,
                            step=5,
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(CONF_KEY_MAP, default=key_map): TextSelector(
                        TextSelectorConfig(multiline=True)
                    ),
                }
            ),
            errors=errors,
        )
