#!/bin/bash

# 切换到脚本所在目录，保证在任何地方执行此脚本都能正确找到 mkdocs.yml
cd "$(dirname "$0")"

echo "=== 启动 ROS Base 文档本地预览 ==="

# 检查是否存在名为 .venv 的虚拟环境，如果存在则自动激活
if [ -d ".venv" ]; then
    echo "[INFO] 发现 .venv 虚拟环境，正在自动激活..."
    source .venv/bin/activate
fi

# 检查当前环境是否安装了 mkdocs
if ! command -v mkdocs &> /dev/null; then
    echo "[ERROR] 未找到 mkdocs 命令！"
    echo "请先安装依赖: pip install -r requirements.txt"
    exit 1
fi

echo "[INFO] 服务启动中... 启动后请在浏览器打开: http://127.0.0.1:8000"
echo "[INFO] 提示: 您的任何 Markdown 文件修改都会自动热更新。按 Ctrl+C 退出预览。"
echo "======================================="

# 启动本地开发服务器
mkdocs serve
