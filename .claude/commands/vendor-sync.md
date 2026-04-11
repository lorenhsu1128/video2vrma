---
description: 重新產生 vendor-versions.txt，固定 vendor/ 各子專案的 commit hash
---

執行以下步驟：

1. 跑以下 bash 指令：

```bash
{
  for d in vendor/*/; do
    name=$(basename "$d")
    if [ -d "$d/.git" ]; then
      hash=$(cd "$d" && git rev-parse --short HEAD)
      branch=$(cd "$d" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "-")
      echo "$name: $hash ($branch)"
    else
      echo "$name: (not a git repo)"
    fi
  done
} > vendor-versions.txt
```

2. 讀 `vendor-versions.txt` 顯示內容
3. 用 `git diff vendor-versions.txt` 檢查是否有變動
4. 若有變動，回報哪個 vendor 變了，並提醒使用者是否要 commit
