# 使用官方Python基础镜像，支持多架构
FROM --platform=$BUILDPLATFORM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 使用阿里云镜像源加速
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    smartmontools \
    util-linux \
    procps \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用文件
COPY nas_fan_controller.py /app/
COPY fan_config.yaml /app/

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 创建非root用户（可选，但需要适当的权限）
# RUN useradd -r -s /bin/false fancontroller

# 设置权限
RUN chmod +x /app/nas_fan_controller.py


# 配置文件已在镜像中，可通过挂载覆盖

# 默认以守护进程模式运行
CMD ["python3", "/app/nas_fan_controller.py", "--daemon"]
