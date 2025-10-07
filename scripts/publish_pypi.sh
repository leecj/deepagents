#!/usr/bin/env bash

# 这个脚本用于构建并发布 deepagents 到 PyPI。
# 使用方法：scripts/publish_pypi.sh [twine额外参数，例如 --repository testpypi]

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "清理旧的构建产物..."
rm -rf dist build new_deepagents.egg-info

echo "开始构建 wheel 与 sdist..."
python3 -m build

echo "上传到 PyPI..."
python3 -m twine upload "$@" dist/*

echo "发布流程完成。"
