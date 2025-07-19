# NAS风扇控制器 Docker 部署指南

## 多架构支持

本镜像支持多种架构：
- **linux/amd64** (x86_64)
- **linux/arm64** (ARM64/aarch64)

Docker会自动选择适合你系统架构的镜像。

## 快速开始

### 1. 构建镜像
```bash
docker-compose build
```

### 2. 启动容器
```bash
docker-compose up -d
```

### 3. 查看日志
```bash
docker logs nas-fan-controller -f
```

## 手动 Docker 命令

### 构建镜像
```bash
docker build -t nas-fan-controller .
```

### 运行容器
```bash
docker run -d \\
  --name nas-fan-controller \\
  --privileged \\
  --network host \\
  -v /dev:/dev \\
  -v /sys:/sys \\
  -v /proc:/proc:ro \\
  -v ./fan_config.yaml:/app/fan_config.yaml:ro \\
  --restart unless-stopped \\
  czcoder/nas-fan-controller:latest
```

## 常用操作

### 查看实时日志
```bash
docker logs nas-fan-controller -f
```

### 重启容器
```bash
docker-compose restart
```

### 停止容器
```bash
docker-compose down
```

### 进入容器调试
```bash
docker exec -it nas-fan-controller bash
```

### 测试模式运行
```bash
docker exec nas-fan-controller python3 /app/nas_fan_controller.py --test
```

### 发现硬盘
```bash
docker exec nas-fan-controller python3 /app/nas_fan_controller.py --discover
```

## 配置说明

- **配置文件**：默认使用 `fan_config.yaml`（YAML格式，支持注释）
- **兼容性**：也支持 JSON 格式的配置文件
- 修改配置后需要重启容器生效
- 所有日志输出到 Docker 标准输出，可用 `docker logs` 查看

## 注意事项

1. **需要特权模式**：容器使用 `--privileged` 模式才能访问硬件设备
2. **挂载系统目录**：需要挂载 `/dev`、`/sys`、`/proc` 等系统目录
3. **网络模式**：使用 `host` 网络模式确保硬件访问正常
4. **权限要求**：在宿主机上需要有访问硬盘和风扇控制的权限

## 故障排除

### 检查容器状态
```bash
docker ps -a
```

### 查看容器详细信息
```bash
docker inspect nas-fan-controller
```

### 检查健康状态
```bash
docker exec nas-fan-controller python3 /app/nas_fan_controller.py --test
```

## 多架构构建和推送

### 使用脚本构建和推送
```bash
# 登录Docker Hub
docker login

# 执行多架构构建和推送
./build-and-push.sh
```

### 手动多架构构建
```bash
# 创建构建器
docker buildx create --name multiarch --use --bootstrap

# 构建和推送多架构镜像
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag czcoder/nas-fan-controller:latest \
    --tag czcoder/nas-fan-controller:v1.0 \
    --push .

# 验证多架构镜像
docker buildx imagetools inspect czcoder/nas-fan-controller:latest
```

### 使用预构建镜像
```bash
# 直接拉取使用（自动选择架构）
docker pull czcoder/nas-fan-controller:latest

# 指定架构拉取
docker pull --platform linux/amd64 czcoder/nas-fan-controller:latest
docker pull --platform linux/arm64 czcoder/nas-fan-controller:latest
```
