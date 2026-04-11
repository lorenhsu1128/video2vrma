---
id: 0001
slug: conda-run-multiline
title: conda run 不支援含換行的 python -c 參數
date: 2026-04-11
tags: [environment, windows, conda]
---

## 錯誤是什麼

在環境檢查時，使用以下指令：

```bash
conda run -n aicuda python -c "
import importlib, sys
sys.path.insert(0, 'vendor/4d-humans')
...
"
```

conda 直接崩潰，吐出：

```
AssertionError: Support for scripts where arguments contain newlines not implemented.
```

完整錯誤來自 `conda/utils.py:451 wrap_subprocess_call`。

## 為什麼犯

`conda run` 為了在 Windows 上正確啟動子 shell，會用 `wrap_subprocess_call` 重寫指令。
這個實作為了避免 escaping 地獄，直接拒絕含換行的參數。這是 conda 本身的限制，不是
本專案環境的問題，macOS/Linux 的 conda 也可能有類似行為。

我犯這個錯的根因是「把 `conda run` 當成 `bash -c` 用」，忽略了它是跨平台包裝層。

## 未來如何避免

1. **若需要跑多行 Python**：先用 Write 工具建立 `.py` 檔（例如 `tmp_check.py` 或 `scripts/xxx.py`），然後：
   ```bash
   conda run -n aicuda python scripts/xxx.py
   ```
2. **單行 `-c` 仍可用**：只要整個字串不含 `\n`，例如：
   ```bash
   conda run -n aicuda python -c "import torch; print(torch.cuda.is_available())"
   ```
3. **臨時檢查**：寫 `tmp_xxx.py`，跑完後記得刪掉（或加到 `.gitignore`）
4. **若真的想強行用多行**：改走 `conda activate aicuda && python -c "..."` — 但 activate 不能跨 bash call 持久化，所以要在同一個 `bash -c` 裡做

## 如何判斷是否適用

- 所有需要透過 `conda run` 執行 Python 腳本的情境
- 特別是環境檢查、除錯、一次性驗證時，AI 容易順手寫多行 `-c`
- 若未來改用 venv / poetry / uv，此限制消失（但寫成檔案仍然可讀性更好）
