# 心够智家（Xingou）云接口协议分析

来源：反编译「心够智家」Android App `com.ixingoo.xingou` v3.4.3（uni-app + 原生混合，未加固），
以及设备标签信息（IAM M9 Pro，无线模组 **MXCHIP EMC5020**，FogCloud 云模组）。

> 本文件仅供学习与个人设备接入参考，请勿用于非授权访问。

## 1. 基础信息

| 项目 | 值 |
| --- | --- |
| 生产环境 API | `https://xapp.ixingoo.com/xapp/` |
| 预发布 API | `https://pubiot.ixingoo.com/xapp/` |
| 测试 API | `https://test.ixingoo.com/xapp/` |
| H5 域名 | `https://appweb.ixingoo.com` |
| MQTT（设备侧） | `ssl://emqs.ixingoo.com:8883` |
| App 版本 | 3.4.3（请求头 `appVersion`） |
| 设备云模组 | MXCHIP EMC5020（FogCloud 云模组） |

## 2. 鉴权

### 2.1 请求头（所有业务接口）

| Header | 值 |
| --- | --- |
| `token` | 登录后返回的 token |
| `userName` | 登录用户名（手机号） |
| `signStr` | IM 签名（可选，HTTP 接口未强制） |
| `appVersion` | `3.4.3` |
| `osType` | `2`（Android） |
| `phTypeName` | 手机型号（任意字符串即可） |
| `phOSVersion` | 系统版本（任意字符串即可） |

**没有请求签名**，只要 token 有效即可调用。

### 2.2 登录流程

```text
POST /xapp/sms/sendCode
  form: userName=<手机号>&version=1.0.0

POST /xapp/user/quickLogin
  form: userName=<手机号>&code=<验证码>&version=1.0.0
  → result 中包含 token / userId / userName
```

### 2.3 返回格式

```json
{"status": "1", "message": "成功", "result": {...}}
```

| status | 含义 |
| --- | --- |
| `1040` | 登录状态过期，需要重新登录 |
| `5000` | 短信发送失败（号码错误或频率限制） |
| 其它 | 见 message |

## 3. 业务接口

| 功能 | 方法 & 路径 | 参数 |
| --- | --- | --- |
| 首页/设备列表 | `POST index/homepage` | `userId`, `version` |
| 设备详情 | `POST devCustInfo/devInfo` | 见 App 实现 |
| 房间设备 | `POST room/userDevList` | `userId`, `version` |
| **读全部属性** | `POST devOperate/findDevAllProperties` | `deviceId`, `version` |
| **下发指令** | `POST devOperate/operCmd` | JSON: `{"deviceId": "...", "operCmd": {...}}` |
| 开机/关机（专用） | `POST devCustBind/setPowerStatus` | 见 App 实现 |
| OTA | `POST devOTA/firmwareVersion` / `devOTA/upgradeInfo` | `deviceId` |

### 3.1 指令格式

`devOperate/operCmd` 的 body：

```json
{
  "deviceId": "xxxxx",
  "operCmd": {
    "power": 1,
    "speed": 3,
    "mode": "auto"
  }
}
```

`operCmd` 的键就是 `findDevAllProperties` 返回的属性名。不同型号键名可能不同，
建议先用 `findDevAllProperties` 导出一份，再用对应键名下发。

### 3.2 属性格式

`findDevAllProperties` 可能返回以下两种形态之一：

```json
{"result": {"properties": [{"identifier": "pm25", "value": 12}, ...]}}
```

或

```json
{"result": {"pm25": 12, "temperature": 23.5, ...}}
```

集成里的解析器两种都兼容（见 `api.extract_properties`）。

## 4. 设备侧

- 设备通过 **MXCHIP EMC5020** 模组连接 FogCloud/MQTT（`ssl://emqs.ixingoo.com:8883`）
- App 内同时打包了 **阿里云 IoT Link SDK**（`iot-auth.ap-southeast-1.aliyuncs.com`），
  但走 FogCloud 的净化器由 IAM 服务端代理下发，App 只调 `devOperate/operCmd`
- 局域网扫描未发现设备开放 TCP 端口，判断为**纯云端**设备

## 5. 其它发现

- App 内 APP_KEY / APP_SECRET（生产）：`27713098` / `9888fe5e1718999db6f34596eb4d3eb5`
  （用于阿里云 AEP SDK 的应用级鉴权，**HTTP API 不需要**）
- 设备产品 Key（KQ = 空气净化器）：`a1K1xRs5Bn8`
- 米家/天猫精灵：App 内仅有天猫精灵授权入口，没有米家通道
