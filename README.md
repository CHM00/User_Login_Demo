# 用户登录演示系统

本项目是一个基于 **Python 3.12** 开发的高性能用户登录管理演示系统。项目采用现代化的包管理工具 **uv** 进行依赖管理，并提供完整的 **Docker** 容器化部署方案。

---

## 🚀 技术栈
* **语言**: Python 3.12.12
* **Web 框架**: Flask (后端逻辑)
* **WSGI 服务器**: Waitress (生产级部署)
* **图像处理**: Pillow (处理用户头像等)
* **包管理**: [uv](https://github.com/astral-sh/uv) (超快速的 Python 包安装器)
* **容器化**: Docker

---

## 📦 本地开发环境配置

推荐使用 `uv` 以获得最快的环境搭建体验。

### 1. 克隆项目
\`\`\`bash
git clone git@github.com:CHM00/User_Login_Demo.git
cd User_Login_Demo
\`\`\`

### 2. 创建虚拟环境并同步依赖
\`\`\`bash
# uv 会自动根据 pyproject.toml 和 uv.lock 同步环境
uv sync
\`\`\`

### 3. 激活环境
\`\`\`bash
source .venv/bin/activate
\`\`\`

### 4. 运行应用
\`\`\`bash
python app.py
\`\`\`

---

## 🐳 Docker 部署方案

项目已包含优化过的 `Dockerfile`，支持分层构建缓存。

### 1. 构建镜像
\`\`\`bash
docker build -t mangersystem:latest .
\`\`\`

### 2. 运行容器
\`\`\`bash
# 将容器 3389 端口映射至宿主机 3389 端口
docker run -d -p 3389:3389 --name mangersystem-container mangersystem:latest
\`\`\`

### 3. 挂载开发卷 (代码热重载调试)
如果你需要在不重新构建镜像的情况下实时修改代码：
\`\`\`bash
docker run -d -p 3389:3389 -v $(pwd):/app mangersystem:latest
\`\`\`

---

## 📂 项目结构
* `app.py`: 项目主入口
* `pyproject.toml`: 现代化项目定义与依赖约束（要求 Python >= 3.12）
* `uv.lock`: 强一致性依赖锁定文件
* `Dockerfile`: 基于 `python:3.12-slim` 的高效构建配置
* `.python-version`: 指定项目使用的 Python 版本

---

## 📝 开发笔记
* **版本迁移**: 项目已从旧版 Python 成功迁移至 3.12 环境。
* **权限说明**: 远程推送已配置 SSH Key (ed25519) 以确保身份验证安全性。
EOF

# 2. 清理之前误生成的临时文件
rm -f y y.pub

# 3. 提交 README 修改并推送到 GitHub
git add README.md
git commit -m "docs: 完善项目文档，增加 Docker 和 uv 使用说明"
git push
