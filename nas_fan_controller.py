#!/usr/bin/env python3
"""
NAS硬盘温度监控和风扇控制脚本
自动检测硬盘温度并根据温度调节风扇转速
"""

import subprocess
import time
import json
import yaml
import logging
import argparse
import os
import sys
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class DiskTemperatureMonitor:
    """硬盘温度监控类"""
    
    def __init__(self):
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()  # 只输出到控制台，Docker会处理日志
            ]
        )
        return logging.getLogger(__name__)
    
    def get_disk_temperature(self, device: str) -> Optional[int]:
        """
        获取指定硬盘的温度
        
        Args:
            device: 硬盘设备路径，如 /dev/sda
            
        Returns:
            温度值（摄氏度），获取失败返回None
        """
        try:
            # 使用smartctl命令获取硬盘温度
            cmd = ['smartctl', '-A', device]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                self.logger.warning(f"获取 {device} 温度失败: {result.stderr}")
                return None
            
            # 解析温度信息
            for line in result.stdout.split('\n'):
                if 'Temperature_Celsius' in line:
                    parts = line.split()
                    if len(parts) >= 10:
                        try:
                            temperature = int(parts[9])
                            self.logger.debug(f"{device} 温度: {temperature}°C")
                            return temperature
                        except (ValueError, IndexError):
                            continue
                
                # 兼容其他温度显示格式
                if 'Current Drive Temperature' in line:
                    try:
                        temp_str = line.split(':')[1].strip().split()[0]
                        temperature = int(temp_str)
                        self.logger.debug(f"{device} 温度: {temperature}°C")
                        return temperature
                    except (ValueError, IndexError):
                        continue
            
            self.logger.warning(f"无法解析 {device} 的温度信息")
            return None
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"获取 {device} 温度超时")
            return None
        except Exception as e:
            self.logger.error(f"获取 {device} 温度时发生错误: {e}")
            return None
    
    def discover_disks(self) -> List[str]:
        """
        自动发现系统中的硬盘
        
        Returns:
            硬盘设备路径列表
        """
        disks = []
        
        try:
            # 查找/dev/sd*设备
            for device_path in Path('/dev').glob('sd[a-z]'):
                if device_path.is_block_device():
                    disks.append(str(device_path))
            
            # 查找/dev/nvme*设备
            for device_path in Path('/dev').glob('nvme[0-9]n[0-9]'):
                if device_path.is_block_device():
                    disks.append(str(device_path))
            
            self.logger.info(f"发现硬盘: {disks}")
            return sorted(disks)
            
        except Exception as e:
            self.logger.error(f"发现硬盘时发生错误: {e}")
            return []
    
    def get_all_temperatures(self, devices: List[str]) -> Dict[str, int]:
        """
        获取所有指定硬盘的温度
        
        Args:
            devices: 硬盘设备路径列表
            
        Returns:
            设备路径到温度的映射字典
        """
        temperatures = {}
        
        for device in devices:
            temp = self.get_disk_temperature(device)
            if temp is not None:
                temperatures[device] = temp
        
        return temperatures


class FanController:
    """风扇控制类"""

    def __init__(self, fan_ctrl_path: str, fan_speed_path: str, max_value: int = 255):
        self.logger = logging.getLogger(__name__)
        self.fan_ctrl_path = fan_ctrl_path
        self.fan_speed_path = fan_speed_path
        self.max_value = max_value

    def set_fan_speed(self, speed_percent: int) -> bool:
        """
        设置风扇转速

        Args:
            speed_percent: 风扇转速百分比 (0-100)

        Returns:
            设置是否成功
        """
        if not 0 <= speed_percent <= 100:
            self.logger.error(f"无效的风扇转速: {speed_percent}%")
            return False

        pwm_value = int(speed_percent * self.max_value / 100)

        try:
            with open(self.fan_ctrl_path, 'w') as f:
                f.write(str(pwm_value))
            self.logger.info(f"设置 {self.fan_ctrl_path} 风扇转速为 {speed_percent}%")
            return True
        except (PermissionError, FileNotFoundError, OSError) as e:
            self.logger.warning(f"设置 {self.fan_ctrl_path} 失败: {e}")
            return False

    def get_current_speed(self) -> int:
        """获取当前风扇转速百分比（从实际RPM读取）"""
        try:
            with open(self.fan_speed_path, 'r') as f:
                current_speed = int(f.read().strip())
                return int((current_speed / self.max_value) * 100)
        except (PermissionError, FileNotFoundError, OSError, ValueError) as e:
            self.logger.warning(f"读取 {self.fan_speed_path} 失败: {e}")
            return 0
    
    def get_current_pwm_speed(self) -> int:
        """获取当前PWM设置的转速百分比"""
        try:
            with open(self.fan_ctrl_path, 'r') as f:
                pwm_output = f.read().strip()
                
                # 尝试直接解析为整数(标准Linux格式)
                try:
                    current_pwm = int(pwm_output)
                    return int((current_pwm / self.max_value) * 100)
                except ValueError:
                    pass
                
                # 绿联格式: "now 255 of 255 (set 0 ~ 255)"
                import re
                pwm_match = re.search(r'now\s+(\d+)\s+of\s+(\d+)', pwm_output)
                if pwm_match:
                    current_pwm = int(pwm_match.group(1))
                    max_pwm = int(pwm_match.group(2))
                    return int((current_pwm / max_pwm) * 100)
                
                self.logger.warning(f"无法解析PWM输出格式: {pwm_output}")
                return 0
                
        except (PermissionError, FileNotFoundError, OSError) as e:
            self.logger.warning(f"读取 {self.fan_ctrl_path} PWM值失败: {e}")
            return 0
    


class NASFanController:
    """NAS风扇控制主类"""
    
    def __init__(self, config_file: str = 'fan_config.yaml'):
        self.config_file = config_file
        self.config = self._load_config()
        self.temp_monitor = DiskTemperatureMonitor()
        fan_ctrl_path = self.config['fan_control_paths']['fan_ctrl_speed']
        fan_speed_path = self.config['fan_control_paths']['fan_speed']
        pwm_max_value = self.config['pwm_config']['max_value']
        self.fan_controller = FanController(fan_ctrl_path, fan_speed_path, pwm_max_value)
        self.logger = logging.getLogger(__name__)
        
        # 缓存硬盘列表，避免每次都重新发现
        if self.config['disks']:
            self._cached_devices = self.config['disks']
        else:
            self._cached_devices = self.temp_monitor.discover_disks()
        
        self.logger.info(f"监控硬盘列表: {self._cached_devices}")
    
    def _load_config(self) -> Dict:
        """加载配置文件，支持YAML和JSON格式"""
        default_config = {
            "temperature_thresholds": {
                "low": 35,      # 低温阈值
                "medium": 45,   # 中温阈值
                "high": 55,     # 高温阈值
                "critical": 65  # 临界温度
            },
            "fan_speeds": {
                "low": 30,      # 低速30%
                "medium": 50,   # 中速50%
                "high": 70,     # 高速70%
                "critical": 100 # 最高速100%
            },
            "fan_control_paths": {
                "fan_ctrl_speed": "/sys/class/hwmon/hwmon0/pwm1",
                "fan_speed": "/sys/class/hwmon/hwmon0/fan1_input"
            },
            "pwm_config": {
                "max_value": 255,     # PWM最大值（绿联为255，标准Linux通常为255）
                "max_rpm": None       # 风扇最大转速（可选，用于精确计算百分比）
            },
            "check_interval": 30,  # 检查间隔（秒）
            "disks": [],          # 要监控的硬盘，空列表表示自动发现
            "hysteresis": 2       # 温度滞后值，防止频繁切换
        }
        
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    # 根据文件扩展名选择解析器
                    if self.config_file.endswith(('.yaml', '.yml')):
                        user_config = yaml.safe_load(f)
                    else:
                        user_config = json.load(f)
                    
                    if user_config:
                        default_config.update(user_config)
                    print(f"已加载配置文件: {self.config_file}")
                    
            except Exception as e:
                print(f"加载配置文件失败，使用默认配置: {e}")
        else:
            # 创建默认配置文件
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    if self.config_file.endswith(('.yaml', '.yml')):
                        yaml.dump(default_config, f, default_flow_style=False, 
                                allow_unicode=True, indent=2)
                    else:
                        json.dump(default_config, f, indent=2, ensure_ascii=False)
                print(f"已创建默认配置文件: {self.config_file}")
            except Exception as e:
                print(f"创建配置文件失败: {e}")
        
        return default_config
    
    def calculate_fan_speed(self, max_temp: int, current_fan_speed: int) -> int:
        """
        根据最高温度计算所需的风扇转速
        
        Args:
            max_temp: 当前最高温度
            current_fan_speed: 当前风扇转速
            
        Returns:
            建议的风扇转速百分比
        """
        thresholds = self.config['temperature_thresholds']
        speeds = self.config['fan_speeds']
        hysteresis = self.config['hysteresis']
        
        # 根据温度确定基础转速
        if max_temp >= thresholds['critical']:
            base_speed = speeds['critical']
        elif max_temp >= thresholds['high']:
            base_speed = speeds['high']
        elif max_temp >= thresholds['medium']:
            base_speed = speeds['medium']
        elif max_temp >= thresholds['low']:
            base_speed = speeds['low']
        else:
            base_speed = speeds['low']
        
        # 应用滞后逻辑，防止频繁切换
        if abs(base_speed - current_fan_speed) <= hysteresis:
            return current_fan_speed
        
        return base_speed
    
    def run_once(self) -> Tuple[Dict[str, int], int, int]:
        """
        执行一次温度检查和风扇调节
        
        Returns:
            (温度字典, 最高温度, 设置的风扇转速)
        """
        # 使用缓存的硬盘列表
        devices = self._cached_devices
        
        if not devices:
            self.logger.error("未发现任何硬盘设备")
            return {}, 0, 0
        
        # 获取温度
        temperatures = self.temp_monitor.get_all_temperatures(devices)
        
        if not temperatures:
            self.logger.error("无法获取任何硬盘温度")
            return {}, 0, 0
        
        # 计算最高温度
        max_temp = max(temperatures.values())
        
        # 获取当前实际的PWM设置值
        current_speed = self.fan_controller.get_current_pwm_speed()
        if current_speed == 0:  # 如果读取失败，使用默认值
            current_speed = self.config['fan_speeds']['low']
        
        # 确定温度档位
        thresholds = self.config['temperature_thresholds']
        if max_temp >= thresholds['critical']:
            temp_level = "临界高温"
        elif max_temp >= thresholds['high']:
            temp_level = "高温"
        elif max_temp >= thresholds['medium']:
            temp_level = "中温"
        elif max_temp >= thresholds['low']:
            temp_level = "低温"
        else:
            temp_level = "超低温"
        
        # 计算新的风扇转速
        new_speed = self.calculate_fan_speed(max_temp, current_speed)
        
        # 设置风扇转速
        if new_speed != current_speed:
            self.logger.info(f"温度: {max_temp}°C ({temp_level}), 当前PWM: {current_speed}%, 目标PWM: {new_speed}%")
            if self.fan_controller.set_fan_speed(new_speed):
                self.logger.info(f"风扇转速调整: {current_speed}% -> {new_speed}%")
                # 等待风扇转速稳定
                time.sleep(3)  # 等待3秒让风扇加速/减速到目标转速
            else:
                self.logger.error("设置风扇转速失败")
        
        # 记录状态
        temp_info = ', '.join([f"{dev}: {temp}°C" for dev, temp in temperatures.items()])
        
        # 获取实际RPM信息（如果可能）
        rpm_info = ""
        try:
            with open(self.config['fan_control_paths']['fan_speed'], 'r') as f:
                fan_output = f.read().strip()
                if 'RPM' in fan_output:
                    # 绿联格式: "fan speed:720 RPMnow 92 of 255 (set 0 ~ 255)"
                    import re
                    rpm_match = re.search(r'(\d+)\s*RPM', fan_output)
                    if rpm_match:
                        current_rpm = int(rpm_match.group(1))
                        max_rpm = self.config['pwm_config'].get('max_rpm')
                        if max_rpm:
                            actual_percent = int((current_rpm / max_rpm) * 100)
                            rpm_info = f", 实际: {current_rpm}RPM({actual_percent}%)"
                        else:
                            rpm_info = f", 实际: {current_rpm}RPM"
                else:
                    # 标准Linux格式：直接RPM数值
                    current_rpm = int(fan_output)
                    max_rpm = self.config['pwm_config'].get('max_rpm')
                    if max_rpm:
                        actual_percent = int((current_rpm / max_rpm) * 100)
                        rpm_info = f", 实际: {current_rpm}RPM({actual_percent}%)"
                    else:
                        rpm_info = f", 实际: {current_rpm}RPM"
        except Exception:
            pass  # 如果无法读取RPM，就不显示
            
        self.logger.info(f"硬盘温度: {temp_info}, 最高: {max_temp}°C, PWM: {new_speed}%{rpm_info}")
        
        return temperatures, max_temp, new_speed
    
    def run_daemon(self):
        """以守护进程模式运行"""
        self.logger.info("启动NAS风扇控制守护进程")
        
        # UGreen风扇控制器不需要手动启用
        
        try:
            while True:
                self.run_once()
                time.sleep(self.config['check_interval'])
                
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，正在退出...")
        except Exception as e:
            self.logger.error(f"守护进程发生错误: {e}")
        finally:
            # 恢复风扇到安全转速
            self.fan_controller.set_fan_speed(self.config['fan_speeds']['medium'])
            self.logger.info("已恢复风扇到安全转速")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='NAS硬盘温度监控和风扇控制')
    parser.add_argument('-c', '--config', default='fan_config.yaml',
                       help='配置文件路径 (支持YAML和JSON格式，默认: fan_config.yaml)')
    parser.add_argument('-d', '--daemon', action='store_true',
                       help='以守护进程模式运行')
    parser.add_argument('--test', action='store_true',
                       help='测试模式，只运行一次')
    parser.add_argument('--discover', action='store_true',
                       help='发现硬盘并显示温度')
    
    args = parser.parse_args()
    
    # 支持通过环境变量控制运行模式（方便Docker部署）
    run_mode = os.getenv('RUN_MODE', 'daemon').lower()
    if not any([args.daemon, args.test, args.discover]):
        if run_mode == 'test':
            args.test = True
        elif run_mode == 'discover':
            args.discover = True
        else:  # 默认为daemon模式
            args.daemon = True
    
    # 检查是否以root权限运行
    if os.geteuid() != 0:
        print("警告: 建议以root权限运行此脚本以确保能够控制风扇")
    
    controller = NASFanController(args.config)
    
    if args.discover:
        # 发现硬盘模式
        monitor = DiskTemperatureMonitor()
        disks = monitor.discover_disks()
        if disks:
            print("发现的硬盘设备:")
            for disk in disks:
                temp = monitor.get_disk_temperature(disk)
                status = f"{temp}°C" if temp is not None else "无法获取温度"
                print(f"  {disk}: {status}")
        else:
            print("未发现任何硬盘设备")
    
    elif args.test:
        # 测试模式
        print("测试模式 - 执行一次检查...")
        temps, max_temp, fan_speed = controller.run_once()
        print(f"硬盘温度: {temps}")
        print(f"最高温度: {max_temp}°C")
        print(f"风扇转速: {fan_speed}%")
    
    elif args.daemon:
        # 守护进程模式
        controller.run_daemon()
    
    else:
        print("请指定运行模式: --daemon, --test, 或 --discover")
        print("使用 --help 查看详细帮助")


if __name__ == '__main__':
    main()
