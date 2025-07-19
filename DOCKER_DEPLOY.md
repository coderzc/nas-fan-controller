# Docker部署说明

## 🚀 Docker镜像已更新

### 最新版本特性

- ✅ **多架构支持**: AMD64 + ARM64 (支持绿联4300 Plus等ARM设备)
- ✅ **通用配置**: 默认使用标准Linux PWM路径，兼容性更好
- ✅ **可配置化**: 通过配置文件轻松适配不同硬件
- ✅ **智能温控**: 基于硬盘温度自动调节风扇转速

## 快速部署

### 1. 使用docker-compose (推荐)

```bash
# 下载配置文件
wget https://raw.githubusercontent.com/coderzc/nas-fan-controller/main/docker-compose.yml
wget https://raw.githubusercontent.com/coderzc/nas-fan-controller/main/fan_config.yaml

# 启动服务
docker-compose up -d
```

### 2. 直接运行Docker容器

```bash
docker run -d \
  --name nas-fan-controller \
  --privileged \
  --restart unless-stopped \
  --network host \
  -v /dev:/dev \
  -v /sys:/sys \
  -v /proc:/proc:ro \
  -v $(pwd)/fan_config.yaml:/app/fan_config.yaml:ro \
  -e TZ=Asia/Shanghai \
  czcoder/nas-fan-controller:latest
```

## 硬件配置

### 绿联4300 Plus用户

修改 `fan_config.yaml` 中的路径：

```yaml
fan_control_paths:
  fan_ctrl_speed: /sys/devices/platform/ug-fan/fan_ctrl_speed
  fan_speed: /sys/devices/platform/ug-fan/fan_speed
```

### 其他硬件用户

1. **查找PWM控制路径**:
   ```bash
   find /sys -name "pwm*" 2>/dev/null
   find /sys -name "fan*_input" 2>/dev/null
   ```

2. **修改配置**:
   ```yaml
   fan_control_paths:
     fan_ctrl_speed: /sys/class/hwmon/hwmon0/pwm1
     fan_speed: /sys/class/hwmon/hwmon0/fan1_input
   ```

## 监控和调试

### 查看日志
```bash
docker logs -f nas-fan-controller
```

### 发现硬盘和温度
首先运行发现模式来查看系统中的硬盘：

```bash
docker exec nas-fan-controller python3 /app/nas_fan_controller.py --discover
```

### 测试单次运行
执行一次温度检查和风扇调节：

```bash
docker exec nas-fan-controller python3 /app/nas_fan_controller.py --test
```

### 守护进程模式
持续运行监控：

```bash
docker exec nas-fan-controller python3 /app/nas_fan_controller.py --daemon
```

### 检查健康状态
```bash
docker ps  # 查看健康状态
```

## 配置调优

### 温度阈值
```yaml
temperature_thresholds:
  low: 35       # 35°C以下
  medium: 45    # 35-45°C
  high: 55      # 45-55°C  
  critical: 65  # 55°C以上
```

### 风扇转速
```yaml
fan_speeds:
  low: 30       # 低温时30%转速
  medium: 50    # 中温时50%转速
  high: 70      # 高温时70%转速
  critical: 100 # 临界温度时100%转速
```

### 检查间隔
```yaml
check_interval: 10  # 每10秒检查一次温度
```

## 故障排除

### 1. 权限问题
确保容器运行在特权模式(`--privileged`)

### 2. 路径不存在
检查风扇控制路径是否正确：
```bash
ls -la /sys/class/hwmon/
ls -la /sys/devices/platform/
```

### 3. 硬盘温度获取失败
确保安装了smartmontools并且硬盘支持SMART

### 4. 风扇不转动
1. 检查风扇控制路径
2. 验证PWM值范围(通常0-255)
3. 检查硬件是否支持软件控制

## 更新镜像

```bash
docker pull czcoder/nas-fan-controller:latest
docker-compose down
docker-compose up -d
```

## 支持的架构

- ✅ linux/amd64 (Intel/AMD 64位)
- ✅ linux/arm64 (ARM 64位，如绿联NAS)

镜像地址: `czcoder/nas-fan-controller:latest`
