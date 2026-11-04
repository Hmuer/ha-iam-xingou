# IAM Xingou (心够智家) — Home Assistant 集成

把 **IAM 空气净化器**（以及其它接入「心够智家」云平台的设备）接入 Home Assistant 的非官方集成。

> 通过复刻「心够智家」Android App 的云端接口实现，不依赖米家、不依赖天猫精灵、不需要 root。
> 目前已在 **IAM M9 Pro** 上完成协议验证（设备通过 MXCHIP EMC5020 / FogCloud 云模组联网）。

---

## 功能

- 📱 **手机号 + 短信验证码登录**（配置向导里完成，token 会保存在 HA 里）
- 🌡️ **传感器**：PM2.5、PM10、TVOC、甲醛、CO2、温度、湿度、滤芯寿命、AQI 等
  （云端返回什么属性就生成什么传感器，未识别的属性也会以原始键名暴露）
- 🌬️ **fan 实体**：开关、风速档位（百分比映射）、工作模式（preset）
- 🔘 **binary_sensor / select**：布尔属性与模式属性
- ⚙️ **服务** `iam_xingou.oper_cmd`：下发任意原始属性指令，方便调试和补位
- 🔁 **自动重新认证**：token 过期时 HA 会提示重新登录
- 🧪 **调试工具** `tools/dump_properties.py`：不装 HA 也能导出设备的全部属性

---

## 安装（HACS 自定义仓库）

1. 打开 HACS → 右上角 ⋮ → **Custom repositories**
2. 仓库地址填：`https://github.com/<你的用户名>/ha-iam-xingou`
3. Category 选择 **Integration**，点击 Add
4. 在 HACS 里搜索 **IAM Xingou** 并下载
5. 重启 Home Assistant

> 也可以手动安装：把 `custom_components/iam_xingou` 复制到 HA 的 `config/custom_components/` 下并重启。

## 配置

1. 设置 → 设备与服务 → **添加集成** → 搜索 **IAM Xingou**
2. 输入注册「心够智家」的**手机号**
3. 输入收到的**短信验证码**（约 5 分钟有效）
4. 勾选要接入的净化器
5. 完成，实体自动生成

## 实体说明

| 平台 | 说明 |
| --- | --- |
| `fan.*` | 净化器主实体：开关 / 风速 / 模式 |
| `sensor.*` | 数值属性（PM2.5、温度、湿度、滤芯寿命…） |
| `binary_sensor.*` | 布尔属性 |
| `select.*` | 文本模式属性 |

风速百分比按 1–5 档线性映射（见 `custom_components/iam_xingou/fan.py` 的 `SPEED_RANGE`），
如果实际档位不是 5 档，修改该常量即可。

## 服务

`iam_xingou.oper_cmd`——向设备下发原始指令：

```yaml
service: iam_xingou.oper_cmd
data:
  device_id: "云端设备ID"
  command:
    power: 1
    speed: 3
```

## 选项

- **轮询间隔**：默认 60 秒，可调 15–900 秒
- **属性键映射（JSON）**：预留给不同型号做键名覆盖

## 调试

```bash
python3 tools/dump_properties.py --phone 138xxxxxxxx
```

会打印设备列表和每个设备的完整属性 JSON。把输出贴到 issue 里可以帮忙完善其它型号的映射。

也可以在 HA 里下载 **诊断信息**（设置 → 设备与服务 → IAM Xingou → 下载诊断信息），token 会自动打码。

## 常见问题

| 现象 | 原因 / 处理 |
| --- | --- |
| 短信发送失败 | 手机号格式、发送频率限制；稍等 1 分钟重试 |
| 验证码错误 | 验证码 5 分钟过期；重新发起登录 |
| 一直"登录状态过期" | token 失效，HA 会弹出重新认证 |
| 属性显示成原始键名 | 该型号的属性名尚未加入映射，用 `oper_cmd` 服务或提 issue |
| 没有 `fan` 实体 | 属性里没有识别到电源/风速键，请用诊断信息反馈 |

## 免责声明

- 本项目为个人自用的非官方集成，**与 IAM / 心够科技无关**
- 使用的是 App 自身调用的云端接口，接口可能随 App 更新而失效
- 请仅用于自己账号下的设备；不要用于访问他人设备
- 作者不对使用后果负责

## License

MIT
