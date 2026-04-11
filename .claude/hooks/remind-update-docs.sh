#!/usr/bin/env bash
# PostToolUse hook: 編輯 backend/frontend 原始碼後，提醒 Claude 檢查文件同步。
# 此 hook 不阻擋，只輸出提醒文字（PostToolUse stdout 會送回 Claude 的 context）。

set -euo pipefail

input=$(cat)

path=$(printf '%s' "$input" \
  | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' \
  | head -1 \
  | sed -E 's/.*"file_path"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/')

if [ -z "$path" ]; then
  exit 0
fi

norm="${path//\\//}"
lower=$(printf '%s' "$norm" | tr '[:upper:]' '[:lower:]')

case "$lower" in
  */backend/app/*|backend/app/*|*/frontend/src/*|frontend/src/*)
    cat <<'EOF'
[reminder from .claude/hooks/remind-update-docs.sh]

你剛編輯了 backend/app/ 或 frontend/src/ 下的檔案。完成當前任務單元後，請檢查：

1. DEVELOPMENT_PLAN.md 對應 Phase 的任務勾選是否需要更新（/update-plan）
2. 若新增了 API 端點、服務模組、React 元件，CLAUDE.md「目錄結構」或「API 規格」是否需要同步
3. 若此次修改是為了修正一個會重複犯的錯誤，請寫一條 lesson（/save-lesson）

這是提醒，不是阻擋；繼續你的工作即可。
EOF
    ;;
  */development_plan.md|development_plan.md)
    echo "[reminder] 你剛更新了 DEVELOPMENT_PLAN.md。若 Phase 切換，也別忘了同步 CLAUDE.md 的目錄/API 段落。"
    ;;
esac

exit 0
