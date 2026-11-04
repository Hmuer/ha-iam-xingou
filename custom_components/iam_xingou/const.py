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
    "powerstate", "power", "Power", "powerSwitch", "PowerSwitch", "switch",
    "Switch", "onOff", "OnOff", "deviceSwitch", "mainSwitch",
)
SPEED_KEYS = (
    "windspeed", "speed", "Speed", "windSpeed", "fanSpeed", "windLevel",
    "gear", "fanLevel", "level",
)
MODE_KEYS = (
    "mode", "Mode", "workMode", "WorkMode", "pattern", "runMode",
    "workingMode", "sceneMode",
)
PM25_KEYS = ("PM25", "pm25", "pm2p5", "pm2_5", "PM2P5", "pm2.5")
PM10_KEYS = ("PM10", "pm10")
PM1_KEYS = ("PM1", "pm1")
TVOC_KEYS = ("tvoc", "TVOC", "voc", "VOC", "vocValue")
HCHO_KEYS = ("HCHO", "hcho", "formaldehyde", "ch2o", "CH2O")
CO2_KEYS = ("co2", "CO2", "carbonDioxide")
TEMP_KEYS = ("CuTemperature", "temp", "Temp", "temperature", "Temperature", "indoorTemp")
HUMIDITY_KEYS = ("CurrentHumidity", "humidity", "Humidity", "rh", "RH", "humid")
FILTER_KEYS = (
    "filterLife", "filter", "Filter", "filterPercent", "filterLeft",
    "filterLifePercent", "filterRemain", "lifePercent", "filterStatusOne",
    "filterStatusTwo",
)
FILTER_RUNTIME_KEYS = ("FilterRunTime1", "FilterRunTime2", "filterRunTime")
AQI_KEYS = ("airQualityGrade", "aqi", "AQI", "airQuality", "airQualityIndex")

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

# Friendly names for property keys observed on real IAM devices.
REAL_KEY_LABELS = {
    "powerstate": "电源",
    "windspeed": "风速",
    "mode": "模式",
    "PM1": "PM1.0",
    "PM25": "PM2.5",
    "PM10": "PM10",
    "PM1Level": "PM1.0 等级",
    "PM25Level": "PM2.5 等级",
    "PM10Level": "PM10 等级",
    "HCHO": "甲醛",
    "HCHOLevel": "甲醛等级",
    "CuTemperature": "温度",
    "CurrentHumidity": "湿度",
    "airQualityGrade": "空气质量等级",
    "T_ON_AQIGrade": "开机空气质量阈值",
    "T_OFF_AQIGrade": "关机空气质量阈值",
    "FilterRunTime1": "滤芯1使用时长",
    "FilterRunTime2": "滤芯2使用时长",
    "filterStatusOne": "滤芯1状态",
    "filterStatusTwo": "滤芯2状态",
    "AllergenLevel": "过敏原等级",
    "IonsSwitch": "负离子",
    "MoodLightLevel": "氛围灯",
    "OSD": "屏幕显示",
    "childLockOnOff": "童锁",
    "errorCode": "故障码",
    "TimingOn": "定时开机",
    "TimingOff": "定时关机",
    "RemainingTime": "剩余时间",
    "RunTime": "累计运行时间",
    "TrustSwitch": "信任模式",
    "ForceUnbind": "强制解绑",
    "KJProductType": "产品类型",
}

PLATFORMS = ["sensor", "binary_sensor", "select", "fan"]
