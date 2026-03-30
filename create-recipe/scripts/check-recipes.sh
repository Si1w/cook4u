#!/bin/bash
# 检查 .recipes/ 目录是否存在，并列出已有菜谱文件名（去掉 .md 后缀）

RECIPE_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)/.recipes"

if [ ! -d "$RECIPE_DIR" ]; then
  echo "NO_RECIPE_DIR"
  exit 0
fi

files=$(ls "$RECIPE_DIR"/*.md 2>/dev/null)

if [ -z "$files" ]; then
  echo "EMPTY"
  exit 0
fi

echo "EXISTS"
for f in $files; do
  basename "$f" .md
done
