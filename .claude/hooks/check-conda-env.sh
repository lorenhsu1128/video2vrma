#!/usr/bin/env bash
# PreToolUse hook: 檢查 Bash 指令是否誤用 base 環境的 python/pip，
# 以及攔截 `conda run ... python -c` 含換行的用法（conda run 不支援，見 lesson 0001）。

set -euo pipefail

input=$(cat)

# 從 tool_input.command 取出指令字串
cmd=$(printf '%s' "$input" \
  | python -c "import json,sys
try:
    d=json.load(sys.stdin)
    print(d.get('tool_input',{}).get('command',''))
except Exception:
    print('')" 2>/dev/null || true)

# 若 python 不可用，退回 grep 解析（較粗略）
if [ -z "$cmd" ]; then
  cmd=$(printf '%s' "$input" \
    | grep -oE '"command"[[:space:]]*:[[:space:]]*"[^"]*"' \
    | head -1 \
    | sed -E 's/.*"command"[[:space:]]*:[[:space:]]*"(.*)"$/\1/')
fi

if [ -z "$cmd" ]; then
  exit 0
fi

# ---- 檢查 1: conda run ... python -c 含換行 ----
if printf '%s' "$cmd" | grep -qE 'conda[[:space:]]+run'; then
  if printf '%s' "$cmd" | grep -q 'python[[:space:]]*-c'; then
    # 判斷指令字串中是否有換行
    if printf '%s' "$cmd" | grep -q $'\n'; then
      {
        echo "BLOCKED by .claude/hooks/check-conda-env.sh"
        echo ""
        echo "conda run 不支援含換行的 python -c 參數（見 .claude/lessons/0001-conda-run-multiline.md）。"
        echo "請將多行程式碼寫入檔案後執行："
        echo "  1. 用 Write 建立 scripts/xxx.py 或 tmp_check.py"
        echo "  2. 用 conda run -n aicuda python scripts/xxx.py"
      } >&2
      exit 2
    fi
  fi
fi

# ---- 檢查 2: python/pip/uvicorn/pytest 未經 aicuda ----
# 以下情況會觸發警告：
#   - 指令含有獨立的 python / pip / uvicorn / pytest 關鍵字
#   - 但同時不含 aicuda（conda run 或 activate 目標）
# 例外：--version / --help / which / echo 這類 metadata 指令

needs_env=0
if printf '%s' "$cmd" | grep -qE '(^|[[:space:];|&])(python|pip|uvicorn|pytest)([[:space:];|&]|$)'; then
  needs_env=1
fi

if [ "$needs_env" = "1" ]; then
  if printf '%s' "$cmd" | grep -qE '(aicuda|CONDA_DEFAULT_ENV.*aicuda|activate[[:space:]]+aicuda)'; then
    exit 0
  fi
  # 允許 metadata 類查詢
  if printf '%s' "$cmd" | grep -qE '(--version|--help|[[:space:]]which[[:space:]])'; then
    exit 0
  fi
  {
    echo "BLOCKED by .claude/hooks/check-conda-env.sh"
    echo ""
    echo "偵測到 python/pip/uvicorn/pytest 指令未透過 aicuda 環境執行："
    echo "  $cmd"
    echo ""
    echo "正確用法："
    echo "  conda run -n aicuda <你的指令>"
    echo "  或先 conda activate aicuda 再跑"
    echo ""
    echo "若此指令確實該在 base 環境跑（極少數情況），請與使用者確認後暫停此 hook。"
  } >&2
  exit 2
fi

exit 0
