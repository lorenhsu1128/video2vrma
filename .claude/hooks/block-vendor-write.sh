#!/usr/bin/env bash
# PreToolUse hook: 阻擋寫入 vendor/ 的任何操作。
# vendor/ 是第三方專案的只讀拷貝，客製化寫在 backend/app/services/ 或 frontend/src/services/ 的 adapter 層。
# 若真的需要 patch vendor，使用者需手動取消此 hook 或 hook 設定中移除本項。

set -euo pipefail

input=$(cat)

# 從 tool_input 取 file_path（Write / Edit / MultiEdit 都用此欄位）
path=$(printf '%s' "$input" \
  | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' \
  | head -1 \
  | sed -E 's/.*"file_path"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/')

if [ -z "$path" ]; then
  exit 0
fi

# 正規化路徑：backslash -> slash，並轉小寫以容忍 Windows 大小寫
norm="${path//\\//}"
lower=$(printf '%s' "$norm" | tr '[:upper:]' '[:lower:]')

case "$lower" in
  */vendor/*|vendor/*)
    {
      echo "BLOCKED by .claude/hooks/block-vendor-write.sh"
      echo ""
      echo "目標路徑: $path"
      echo ""
      echo "vendor/ 是第三方專案的只讀拷貝，不得修改。"
      echo "正確做法："
      echo "  - Python 客製化: 在 backend/app/services/ 寫 adapter/wrapper"
      echo "  - TypeScript 客製化: 在 frontend/src/services/ 重寫或包裝"
      echo "  - 若發現 vendor 有 bug 需要修: 開 issue 給上游，或在 services 層 patch"
      echo ""
      echo "若你確信需要修改 vendor（例如手動合上游 patch），請與使用者確認後，"
      echo "暫時在 .claude/settings.json 註解此 hook。"
    } >&2
    exit 2
    ;;
esac

exit 0
