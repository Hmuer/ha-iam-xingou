"""Constants for the IAM Xingou integration."""

DOMAIN = "iam_xingou"

# Cloud endpoints (reverse engineered from the official Android app v3.4.3)
BASE_URL = "https://xapp.ixingoo.com/xapp/"
APP_VERSION = "3.4.3"
LOGIN_VERSION = "1.0.0"

# Config entry keys
CONF_PHONE = "phone"
CONF_CODE = "code"
CONF_TOKEN = "token"
CONF_USER_NAME = "user_name"
CONF_USER_ID = "user_id"
CONF_DEVICES = "devices"
CONF_DOMAIN_ID = "domain_id"
CONF_DEVICE_ID = "device_id"
CONF_DEVICE_NAME = "device_name"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_KEY_MAP = "key_map"

DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 15
MAX_SCAN_INTERVAL = 900

# Candidate property names used to recognise well known functions.
# The integration stays data driven: unknown properties are still exposed
# as plain sensors, and these aliases only decide the *type* of the entity.
POWER_KEYS = (
    "power", "Power", "powerSwitch", "PowerSwitch", "switch", "Switch",
    "onOff", "OnOff", "deviceSwitch", "mainSwitch",
)
SPEED_KEYS = (
    "speed", "Speed", "windSpeed", "fanSpeed", "windLevel", "gear",
    "fanLevel", "windspeed", "level",
)
MODE_KEYS = (
    "mode", "Mode", "workMode", "WorkMode", "pattern", "runMode",
    "workingMode", "sceneMode",
)
PM25_KEYS = ("pm25", "PM25", "pm2p5", "pm2_5", "PM2P5", "pm2.5")
PM10_KEYS = ("pm10", "PM10")
TVOC_KEYS = ("tvoc", "TVOC", "voc", "VOC", "vocValue")
HCHO_KEYS = ("hcho", "HCHO", "formaldehyde", "ch2o", "CH2O")
CO2_KEYS = ("co2", "CO2", "carbonDioxide")
TEMP_KEYS = ("temp", "Temp", "temperature", "Temperature", "indoorTemp")
HUMIDITY_KEYS = ("humidity", "Humidity", "rh", "RH", "humid")
FILTER_KEYS = (
    "filterLife", "filter", "Filter", "filterPercent", "filterLeft",
    "filterLifePercent", "filterRemain", "lifePercent",
)
AQI_KEYS = ("aqi", "AQI", "airQuality", "airQualityIndex")

NUMERIC_UNIT_MAP = {
    "pm25": "µg/m³",
    "pm10": "µg/m³",
    "tvoc": "µg/m³",
    "hcho": "mg/m³",
    "co2": "ppm",
    "temperature": "°C",
    "humidity": "%",
    "filterLife": "%",
    "aqi": "",
}

# Entity names for well known keys (Chinese friendly names)
KEY_LABELS = {
    "pm25": "PM2.5",
    "pm10": "PM10",
    "tvoc": "TVOC",
    "hcho": "甲醛",
    "co2": "CO2",
    "temperature": "温度",
    "humidity": "湿度",
    "filterLife": "滤芯寿命",
    "aqi": "空气质量指数",
    "speed": "风速",
    "mode": "模式",
    "power": "电源",
}

PLATFORMS = ["sensor", "binary_sensor", "select", "fan"]
