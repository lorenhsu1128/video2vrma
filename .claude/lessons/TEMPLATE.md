---
id: NNNN
slug: short-slug
title: 一句話標題
date: YYYY-MM-DD
tags: [environment, vendor, windows, numpy, cuda]
---

## 錯誤是什麼

具體描述當時 AI 做錯了什麼、使用者如何糾正。
要包含足夠細節讓未來對話的 AI 一看就知道這件事發生過。

範例：
> 在執行環境檢查時，使用 `conda run -n aicuda python -c "..."` 傳入多行字串，conda
> 噴出 `AssertionError: Support for scripts where arguments contain newlines not implemented`。

## 為什麼犯

說明根因。不是「指令打錯」這種表面敘述，而是背後的系統原因。

範例：
> conda run 在 Windows 上透過 wrap_subprocess_call 重寫指令，這個實作不支援含換行的參數。
> 這是 conda 本身的限制，不是我們環境的問題。

## 未來如何避免

給出可執行的具體規則。

範例：
> - 若需要跑多行 Python，先用 Write 工具建立 .py 檔，再 `conda run -n aicuda python scripts/xxx.py`
> - 單行 `-c` 仍可用，只要不含 `\n`
> - 若只是臨時檢查，寫 `tmp_check.py` 然後用完刪掉

## 如何判斷是否適用

描述這條 lesson 會在什麼情境觸發。

範例：
> 任何時候需要在 Windows 上透過 conda 執行 Python 腳本時。
> 如果未來改用 macOS/Linux，此限制**可能**消失，但寫成檔案仍是更可靠的做法。
