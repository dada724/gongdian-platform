# 工电中心一体化平台

城轨工电中心生产管理平台，基于 FastAPI + 原生 JS 开发。

## 功能模块

- 🔐 用户登录 / 注册（developer 角色可后台管理）
- 👥 用户管理（增删改查、角色分配、模块权限）
- 📊 生产看板 / 安全看板 / 党群看板
- 📋 会议管理 / 故障管理 / 生产调度工作台
- 📤 用户批量导入 / 导出（CSV）
- 🧩 模块化自由编辑（拖动排序、增删改）

## 快速启动

```bash
# 1. 安装依赖
cd backend
pip install -r requirements.txt

# 2. 初始化数据库（自动创建）
#    首次启动会自动创建 gongdian.db，并创建 admin/admin123 账号

# 3. 启动服务（绑定 0.0.0.0 允许局域网访问）
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

启动后访问：`http://localhost:8000`

## 局域网访问（手机/其他电脑）

启动时使用 `--host 0.0.0.0`，然后查看本机 IP：

```bash
# Windows
ipconfig  # 找到 IPv4 地址，如 192.168.1.100

# Mac / Linux
ifconfig | grep "inet "
```

其他设备访问：`http://192.168.1.100:8000`

## 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin  | admin123 | developer（全权限） |

## 部署到新电脑

```bash
# 1. 克隆项目
git clone https://github.com/你的用户名/gongdian-platform.git
cd gongdian-platform

# 2. 安装依赖
cd backend && pip install -r requirements.txt

# 3. 启动
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## 技术栈

- **后端**：FastAPI + uvicorn + SQLite
- **前端**：原生 HTML/CSS/JS（无框架依赖）
- **认证**：JWT Token
