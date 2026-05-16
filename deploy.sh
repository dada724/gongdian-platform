#!/usr/bin/env bash
# ============================================================
#  工电中心一体化平台 — 一键部署脚本
#  适用：阿里云 / 腾讯云 CentOS 7+、Ubuntu 18.04+
#  用法：bash deploy.sh
# ============================================================

set -e

APP_NAME="工电中心一体化平台"
BACKEND_DIR="$(cd "$(dirname "$0")/backend" && pwd)"
PRONTEND_DIR="$(cd "$(dirname "$0")/frontend" && pwd)"
PORT=8000

echo "============================================"
echo "  $APP_NAME — 部署脚本"
echo "============================================"
echo ""

# ── 1. 检测 Python ────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "❌ 未检测到 python3，请先安装 Python 3.10+"
  echo "   CentOS: yum install python3 python3-pip"
  echo "   Ubuntu: apt  install python3 python3-pip"
  exit 1
fi
PYTHON=python3
echo "✅ Python: $($PYTHON --version 2>&1)"

# ── 2. 安装 pip 依赖 ──────────────────────────────────────────
echo ""
echo "── 安装 Python 依赖 ──"
$PYTHON -m pip install -q --upgrade pip
$PYTHON -m pip install -q fastapi uvicorn python-multipart python-jose[cryptography] bcrypt
echo "✅ pip 依赖安装完成"

# ── 3. 初始化数据库 ────────────────────────────────────────────
echo ""
echo "── 初始化数据库 ──"
cd "$BACKEND_DIR"
$PYTHON -c "import database; database.init_db(); print('✅ 数据库就绪：', database.DB_PATH)"
cd - > /dev/null

# ── 4. 防火墙开放端口 ─────────────────────────────────────────
echo ""
echo "── 配置防火墙（需要 root 权限）──"
if command -v firewall-cmd &>/dev/null; then
  sudo firewall-cmd --add-port=$PORT/tcp --permanent 2>/dev/null && \
  sudo firewall-cmd --reload 2>/dev/null && \
  echo "✅ firewall-cmd：已开放端口 $PORT" || \
  echo "⚠️  无法配置 firewalld（可跳过）"
elif command -v ufw &>/dev/null; then
  sudo ufw allow $PORT/tcp 2>/dev/null && \
  echo "✅ ufw：已开放端口 $PORT" || \
  echo "⚠️  无法配置 ufw（可跳过）"
else
  echo "⚠️  未检测到 firewalld/ufw，请手动开放端口 $PORT"
fi

# ── 5. 启动说明 ─────────────────────────────────────────────────
echo ""
echo "============================================"
echo "  部署完成！启动方式："
echo "============================================"
echo ""
echo "  【方式一】直接启动（前台，适合测试）"
echo "    cd $BACKEND_DIR"
echo "    python3 main.py"
echo ""
echo "  【方式二】后台启动（生产推荐）"
echo "    cd $BACKEND_DIR"
echo "    nohup python3 -m uvicorn main:app --host 0.0.0.0 --port $PORT > ../logs/backend.log 2>&1 &"
echo "    mkdir -p $(dirname $0)/logs"
echo ""
echo "  【访问地址】"
echo "    前端：http://服务器IP:$PORT/"
echo "    API 文档：http://服务器IP:$PORT/docs"
echo ""
echo "  【首次使用】"
echo "    1. 浏览器打开前端地址"
echo "    2. 注册第一个账号（自动成为 developer）"
echo "    3. 登录后可使用全部功能"
echo "============================================"
