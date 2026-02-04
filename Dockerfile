# 1. 使用官方 Python 3.12 瘦镜像作为基础
FROM python:3.12-slim

# 2. 设置工作目录
WORKDIR /app

# 3. 安装 uv (直接从官方镜像拷贝二进制文件，速度最快)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 4. 设置国内镜像源加速 (针对国内服务器环境)
ENV UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
# 强制使用系统 Python，不创建虚拟环境，减小镜像体积
ENV UV_SYSTEM_PYTHON=1

# 5. 先复制依赖文件 (利用 Docker 缓存层，只要依赖不变，这一步会秒过)
COPY pyproject.toml uv.lock ./

# 6. 安装依赖
RUN uv pip install --system --no-cache -r pyproject.toml

# 7. 复制项目代码
COPY . .

# 8. 暴露端口 (根据你的 Flask/Waitress 配置修改)
EXPOSE 3389

# 9. 启动程序 (假设你的启动文件是 app.py)
CMD ["python", "app.py"]
