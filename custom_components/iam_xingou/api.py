"""Async API client for the IAM / Xingou (心够智家) cloud.

Protocol notes (reverse engineered from the official Android app v3.4.3):

* base URL            https://xapp.ixingoo.com/xapp/
* authentication      POST sms/sendCode  -> SMS
                      POST user/quickLogin -> token
* request headers     token, userName, appVersion, osType, phTypeName, phOSVersion
* devices             POST index/homepage            (userId, version)
* properties          POST devOperate/findDevAllProperties (deviceId, version)
* control             POST devOperate/operCmd        {"deviceId": ..., "operCmd": {...}}
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import APP_VERSION, BASE_URL, LOGIN_VERSION

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 20

SUCCESS_STATUSES = {"0", "1", "200", "0000", "success", "SUCCESS", "ok"}
AUTH_EXPIRED_STATUSES = {"1040", "1041", "401"}


class IamXingouError(Exception):
    """Base error."""


class IamXingouAuthError(IamXingouError):
    """Raised when the token is no longer valid (needs re-login)."""


class IamXingouConnectionError(IamXingouError):
    """Raised on network problems."""


class IamXingouRateLimitError(IamXingouError):
    """Raised when the cloud refuses to send another SMS code (status 1020)."""


def _headers(token: str | None = None, user_name: str | None = None) -> dict[str, str]:
    headers = {
        "User-Agent": "okhttp/3.12.13",
        "appVersion": APP_VERSION,
        "osType": "2",
        "phTypeName": "HomeAssistant",
        "phOSVersion": "1.0",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    if token:
        headers["token"] = token
    if user_name:
        headers["userName"] = user_name
    return headers


def _walk_dicts(data: Any):
    """Yield every dict found in a nested structure."""
    if isinstance(data, dict):
        yield data
        for value in data.values():
            yield from _walk_dicts(value)
    elif isinstance(data, list):
        for item in data:
            yield from _walk_dicts(item)


def _first_key(data: Any, keys: tuple[str, ...]) -> Any:
    """Find the first matching key inside a nested structure."""
    for item in _walk_dicts(data):
        for key in keys:
            if key in item and item[key] not in (None, "", [], {}):
                return item[key]
    return None


class IamXingouApi:
    """Small async wrapper around the Xingou cloud endpoints."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        token: str | None = None,
        user_name: str | None = None,
        user_id: str | None = None,
    ) -> None:
        self._session = session
        self.token = token
        self.user_name = user_name
        self.user_id = user_id

    # ------------------------------------------------------------------ http
    async def _post(
        self,
        path: str,
        data: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        url = BASE_URL + path
        headers = _headers(self.token, self.user_name)
        try:
            async with self._session.post(
                url,
                data=data,
                json=json_body,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            ) as resp:
                resp.raise_for_status()
                payload = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise IamXingouConnectionError(str(err)) from err
        except (TimeoutError, asyncio.TimeoutError) as err:
            raise IamXingouConnectionError("timeout") from err

        if not isinstance(payload, dict):
            raise IamXingouError(f"unexpected response: {payload!r}")

        status = str(payload.get("status", "")).strip()
        message = payload.get("message") or payload.get("msg") or ""
        result = payload.get("result")

        if status in AUTH_EXPIRED_STATUSES:
            raise IamXingouAuthError(message or "login expired")

        if status == "1020":
            raise IamXingouRateLimitError(message or "too many requests")

        if status not in SUCCESS_STATUSES and result is None:
            raise IamXingouError(f"API error {status}: {message}")

        return result

    # ----------------------------------------------------------------- login
    async def async_send_code(self, phone: str) -> None:
        """Ask the cloud to send an SMS verification code."""
        await self._post(
            "sms/sendCode", data={"userName": phone, "version": LOGIN_VERSION}
        )

    async def async_login(self, phone: str, code: str) -> dict[str, Any]:
        """Exchange phone + SMS code for an access token."""
        result = await self._post(
            "user/quickLogin",
            data={"userName": phone, "code": code, "version": LOGIN_VERSION},
        )
        token = _first_key(result, ("token", "accessToken", "userToken"))
        if not token:
            raise IamXingouAuthError("login did not return a token")
        self.token = str(token)
        self.user_id = str(_first_key(result, ("userId", "userid", "id")) or "")
        self.user_name = str(
            _first_key(result, ("userName", "username", "phone")) or phone
        )
        return result if isinstance(result, dict) else {"result": result}

    # --------------------------------------------------------------- devices
    async def async_homepage(self) -> Any:
        """Return the home page payload containing the user's devices."""
        return await self._post(
            "index/homepage",
            data={"userId": self.user_id or "", "version": APP_VERSION},
        )

    async def async_properties(self, device_id: str) -> Any:
        """Return all current properties of one device."""
        return await self._post(
            "devOperate/findDevAllProperties",
            data={"deviceId": device_id, "version": APP_VERSION},
        )

    async def async_oper_cmd(self, device_id: str, oper_cmd: dict[str, Any]) -> Any:
        """Send a control command to one device."""
        return await self._post(
            "devOperate/operCmd",
            json_body={"deviceId": device_id, "operCmd": oper_cmd},
        )


# ------------------------------------------------------------------ parsers
def extract_devices(home: Any) -> list[dict[str, Any]]:
    """Extract device dictionaries from the homepage payload."""
    devices: dict[str, dict[str, Any]] = {}
    for item in _walk_dicts(home):
        device_id = item.get("deviceId") or item.get("iotId") or item.get("devId")
        if not device_id or not isinstance(device_id, str):
            continue
        if device_id in devices:
            continue
        model = str(
            item.get("productName") or item.get("modelName") or item.get("model") or ""
        )
        name = (
            item.get("deviceName")
            or item.get("devName")
            or item.get("name")
            or item.get("nickName")
        )
        if not name:
            name = "IAM 净化器" if model else f"IAM {device_id[-6:]}"
        devices[device_id] = {
            "device_id": device_id,
            "name": str(name),
            "model": model,
            "raw": item,
        }
    return list(devices.values())


def extract_properties(props: Any) -> dict[str, Any]:
    """Flatten the property payload into a ``{key: value}`` mapping.

    The cloud may answer either with ``{"identifier": "x", "value": 1}``
    entries or with a plain dictionary, so both shapes are supported.
    """
    flat: dict[str, Any] = {}

    def _collect(item: Any) -> None:
        if not isinstance(item, dict):
            return
        key = (
            item.get("identifier")
            or item.get("propertyKey")
            or item.get("key")
            or item.get("name")
            or item.get("code")
        )
        if key and "value" in item:
            flat[str(key)] = item["value"]
            return
        for k, v in item.items():
            if isinstance(v, (dict, list)):
                _collect(v)
            elif not isinstance(v, (dict,)):
                # plain key/value dictionary
                if k not in ("deviceId", "version", "status", "message"):
                    flat.setdefault(str(k), v)

    _collect(props)
    if props and not flat and isinstance(props, dict):
        for k, v in props.items():
            if isinstance(v, (str, int, float, bool)):
                flat[str(k)] = v
    return flat
