#!/usr/bin/env python3
"""Standalone explorer for the Xingou (心够智家) cloud API.

Usage:
    python3 tools/dump_properties.py --phone 138xxxx

The script asks for the SMS code, logs in, prints the device list and dumps
every property of every device. Use the output to verify / adjust the entity
mapping of the Home Assistant integration.

This file is deliberately dependency free (stdlib only) so it also runs on a
NAS / Raspberry Pi without Home Assistant installed.
"""

from __future__ import annotations

import argparse
import getpass
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://xapp.ixingoo.com/xapp/"
APP_VERSION = "3.4.3"
LOGIN_VERSION = "1.0.0"


def request(path, data=None, json_body=None, token=None, user_name=None):
    headers = {
        "User-Agent": "okhttp/3.12.13",
        "appVersion": APP_VERSION,
        "osType": "2",
        "phTypeName": "HomeAssistant",
        "phOSVersion": "1.0",
    }
    if token:
        headers["token"] = token
    if user_name:
        headers["userName"] = user_name

    if json_body is not None:
        body = json.dumps(json_body).encode()
        headers["Content-Type"] = "application/json"
    elif data is not None:
        body = urllib.parse.urlencode(data).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    else:
        body = None

    req = urllib.request.Request(BASE_URL + path, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as err:  # pragma: no cover
        print("HTTP error:", err.code, err.read()[:300], file=sys.stderr)
        raise


def walk_dicts(data):
    if isinstance(data, dict):
        yield data
        for value in data.values():
            yield from walk_dicts(value)
    elif isinstance(data, list):
        for item in data:
            yield from walk_dicts(item)


def find_key(data, keys):
    for item in walk_dicts(data):
        for key in keys:
            if key in item and item[key] not in (None, "", [], {}):
                return item[key]
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phone", required=True, help="phone number registered in Xingou")
    args = parser.parse_args()

    print("sending SMS code ...")
    request("sms/sendCode", data={"userName": args.phone, "version": LOGIN_VERSION})
    code = input("SMS code: ").strip()

    login = request(
        "user/quickLogin",
        data={"userName": args.phone, "code": code, "version": LOGIN_VERSION},
    )
    token = find_key(login, ("token", "accessToken", "userToken"))
    user_id = find_key(login, ("userId", "userid", "id"))
    user_name = find_key(login, ("userName", "username", "phone")) or args.phone
    if not token:
        print("login failed:", json.dumps(login, ensure_ascii=False)[:500])
        return 1
    print("logged in, token:", str(token)[:12], "...")

    home = request(
        "index/homepage",
        data={"userId": user_id or "", "version": APP_VERSION},
        token=token,
        user_name=user_name,
    )
    print("homepage payload:")
    print(json.dumps(home, ensure_ascii=False, indent=2)[:4000])

    devices = {}
    for item in walk_dicts(home):
        device_id = item.get("deviceId") or item.get("iotId")
        if device_id:
            devices.setdefault(device_id, item.get("deviceName") or item.get("name"))
    if not devices:
        print("no devices extracted, inspect the homepage payload above")
        return 1

    for device_id, name in devices.items():
        print("\n=== device", name, device_id, "===")
        props = request(
            "devOperate/findDevAllProperties",
            data={"deviceId": device_id, "version": APP_VERSION},
            token=token,
            user_name=user_name,
        )
        print(json.dumps(props, ensure_ascii=False, indent=2)[:6000])

    print("\nsaved credentials for reuse:")
    print(json.dumps({"token": token, "userName": user_name, "userId": user_id}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
