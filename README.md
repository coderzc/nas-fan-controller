# NAS 风扇控制器

[![Docker Pulls](https://img.shields.io/docker/pulls/czcoder/nas-fan-controller)](https://hub.docker.com/r/czcoder/nas-fan-controller)
[![Docker Image Size](https://img.shields.io/docker/image-size/czcoder/nas-fan-controller)](https://hub.docker.com/r/czcoder/nas-fan-controller)
[![GitHub](https://img.shields.io/github/license/coderzc/nas-fan-controller)](https://github.com/coderzc/nas-fan-controller/blob/main/LICENSE)

基于硬盘温度的智能风扇控制系统，支持多种硬件平台，特别针对NAS设备优化。

## 功能特性

- 🌡️ **自动温度监控**：使用smartctl获取硬盘SMART温度数据
- 🌀 **智能风扇控制**：根据温度阈值自动调节PWM风扇转速
- 🔍 **硬盘自动发现**：自动检测系统中的SATA和NVMe硬盘
- ⚙️ **可配置参数**：温度阈值、风扇转速、检查间隔等均可配置
- 📊 **温度滞后机制**：防止风扇转速频繁切换
- 📝 **详细日志记录**：记录温度变化和风扇调节历史
- 🔧 **多种运行模式**：支持守护进程、测试模式、硬盘发现模式

## 系统要求

- Linux操作系统（推荐Ubuntu、Debian、CentOS等）
- Python 3.6+
- smartmontools包（用于读取硬盘温度）
- root权限（用于控制风扇PWM）

## 安装依赖

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install smartmontools python3 python3-pip
```

### CentOS/RHEL
```bash
sudo yum install smartmontools python3 python3-pip
# 或者在较新版本上：
sudo dnf install smartmontools python3 python3-pip
```

### 验证smartctl安装
```bash
smartctl --version
```

## 使用方法

### 1. 发现硬盘和温度
首先运行发现模式来查看系统中的硬盘：

```bash
sudo python3 nas_fan_controller.py --discover
```

### 2. 测试运行
执行一次温度检查和风扇调节：

```bash
sudo python3 nas_fan_controller.py --test
```

### 3. 守护进程模式
持续运行监控：

```bash
sudo python3 nas_fan_controller.py --daemon
```

### 4. 自定义配置文件
```bash
sudo python3 nas_fan_controller.py --config /path/to/custom_config.json --daemon
```

## 配置文件说明

`fan_config.json`配置文件包含以下参数：

```json
{
  "temperature_thresholds": {
    "low": 35,      // 低温阈值（°C）
    "medium": 45,   // 中温阈值（°C）
    "high": 55,     // 高温阈值（°C）
    "critical": 65  // 临界温度（°C）
  },
  "fan_speeds": {
    "low": 30,      // 低速风扇转速（30%）
    "medium": 50,   // 中速风扇转速（50%）
    "high": 70,     // 高速风扇转速（70%）
    "critical": 100 // 最高速风扇转速（100%）
  },
  "check_interval": 30,  // 检查间隔（秒）
  "disks": [],          // 要监控的硬盘列表，空表示自动发现
  "hysteresis": 2       // 温度滞后值，防止频繁切换
}
```

### 参数调整建议

- **温度阈值**：根据硬盘型号调整，一般机械硬盘安全温度在50°C以下
- **风扇转速**：根据实际噪音承受能力调整
- **检查间隔**：建议20-60秒，太频繁会增加系统负担
- **滞后值**：防止在临界温度附近频繁切换风扇转速

## 设置为系统服务

创建systemd服务文件以实现开机自启：

```bash
sudo nano /etc/systemd/system/nas-fan-controller.service
```

服务文件内容：

```ini
[Unit]
Description=NAS Fan Controller Service
Documentation=https://github.com/your-repo/nas-fan-controller
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/path/to/script/directory
ExecStart=/usr/bin/python3 /path/to/script/directory/nas_fan_controller.py --daemon
ExecStop=/bin/kill -s QUIT $MAINPID
Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=5

# 安全设置
NoNewPrivileges=false
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/path/to/script/directory

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
# 重新加载systemd配置
sudo systemctl daemon-reload

# 启用服务（开机自启）
sudo systemctl enable nas-fan-controller.service

# 启动服务
sudo systemctl start nas-fan-controller.service

# 查看服务状态
sudo systemctl status nas-fan-controller.service

# 查看服务日志
sudo journalctl -u nas-fan-controller.service -f
```

## 故障排除

### 1. 无法获取硬盘温度
- 确保安装了smartmontools：`sudo apt install smartmontools`
- 检查硬盘是否支持SMART：`sudo smartctl -i /dev/sda`
- 确保以root权限运行

### 2. 无法控制风扇
- 确保系统支持PWM风扇控制
- 检查`/sys/class/hwmon/`下是否有PWM控制文件
- 确保以root权限运行
- 某些主板需要在BIOS中启用PWM控制

### 3. 找不到PWM控制文件
检查可用的hwmon设备：
```bash
ls -la /sys/class/hwmon/
find /sys/class/hwmon/ -name "pwm*" -type f
```

### 4. 权限错误
确保脚本以root权限运行：
```bash
sudo python3 nas_fan_controller.py --test
```

### 5. 温度读取异常
手动测试smartctl：
```bash
sudo smartctl -A /dev/sda | grep -i temp
```

## 日志文件

脚本会在运行目录生成`fan_controller.log`日志文件，包含：
- 温度监控记录
- 风扇调速记录
- 错误和警告信息
- 系统状态变化

## 安全注意事项

1. **备份重要数据**：在部署前请确保重要数据已备份
2. **测试环境**：建议先在测试环境中验证脚本功能
3. **温度监控**：定期检查日志确保温度在安全范围内
4. **硬件兼容性**：确认主板和风扇支持PWM控制
5. **紧急停止**：了解如何手动控制风扇作为应急措施

## 手动风扇控制（紧急情况）

如果需要手动控制风扇：

```bash
# 查找PWM控制文件
find /sys/class/hwmon/ -name "pwm*" -type f

# 设置风扇到最高速度（255 = 100%）
echo 255 | sudo tee /sys/class/hwmon/hwmon*/pwm*

# 设置风扇到50%速度（约128）
echo 128 | sudo tee /sys/class/hwmon/hwmon*/pwm*
```

## 许可证

本脚本采用MIT许可证，请参考LICENSE文件。

## 贡献

欢迎提交Issue和Pull Request来改进这个脚本。

## 免责声明

使用本脚本需要您自行承担风险。作者不对因使用本脚本造成的硬件损坏、数据丢失或其他损失负责。请在充分测试后再部署到生产环境。
