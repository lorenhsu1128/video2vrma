#!/usr/bin/env bash
# PreToolUse hook: 阻擋寫入有授權或機密風險的路徑。
# - data/smpl/: SMPL 學術授權模型，不得覆寫或進 git
# - .env / credentials / *.pem / *.key: 任何機密檔

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

block() {
  {
    echo "BLOCKED by .claude/hooks/block-sensitive-write.sh"
    echo ""
    echo "目標路徑: $path"
    echo "原因: $1"
    echo ""
    echo "若真的需要寫入，請與使用者確認後暫時取消此 hook。"
  } >&2
  exit 2
}

case "$lower" in
  */data/smpl/*|data/smpl/*)
    block "data/smpl/ 為 SMPL 授權模型目錄，不得覆寫或產生新檔"
    ;;
  */.env|*/.env.*|.env|.env.*)
    block ".env 為環境變數與機密，不得寫入（.env.example 除外）"
    ;;
  */credentials*|credentials*)
    block "credentials 檔案不得寫入"
    ;;
  *.pem|*.key)
    block "私鑰 / 憑證檔案不得寫入"
    ;;
esac

# .env.example 是允許的
case "$lower" in
  */.env.example|.env.example)
    exit 0
    ;;
esac

exit 0
