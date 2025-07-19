# NAS风扇控制器更新说明

## 🎉 重大更新：支持绿联4300 Plus

### 更新内容

1. **风扇控制路径可配置化**
   - 新增 `fan_control_paths` 配置项
   - 支持不同硬件的风扇控制接口
   - 默认配置适配绿联4300 Plus

2. **专用绿联风扇驱动支持**
   - 使用绿联专用的 `ug-fan` 驱动
   - 控制路径：`/sys/devices/platform/ug-fan/fan_ctrl_speed`
   - 状态读取：`/sys/devices/platform/ug-fan/fan_speed`
   - PWM范围：0-255（对应0-100%转速）

3. **配置文件改进**
   - `fan_config.yaml` 新增风扇控制路径配置
   - 支持其他硬件型号的路径自定义

### 配置示例

```yaml
# 风扇控制路径
fan_control_paths:
  fan_ctrl_speed: /sys/devices/platform/ug-fan/fan_ctrl_speed
  fan_speed: /sys/devices/platform/ug-fan/fan_speed
```

### 使用说明

1. **测试风扇控制**：
   ```bash
   python3 nas_fan_controller.py --test
   ```

2. **运行守护进程**：
   ```bash
   python3 nas_fan_controller.py --daemon
   ```

3. **发现硬盘设备**：
   ```bash
   python3 nas_fan_controller.py --discover
   ```

### 适配其他硬件

如果您使用的是其他型号的NAS，只需修改 `fan_config.yaml` 中的路径：

```yaml
fan_control_paths:
  fan_ctrl_speed: /你的/风扇控制/路径
  fan_speed: /你的/风扇状态/路径
```

### 故障排除

1. **权限问题**：确保以root权限运行
2. **驱动问题**：确认 `ug_fan` 模块已加载
3. **路径问题**：检查风扇控制路径是否存在

### 测试结果

- ✅ 温度监控：正常工作
- ✅ 风扇控制：完全正常工作
- ✅ 程序运行：稳定循环运行

风扇控制从 **❌ 不工作** 变为 **✅ 完全正常工作**！

### 感谢

感谢您的耐心测试，帮助我们找到了绿联4300 Plus的正确风扇控制方法！
