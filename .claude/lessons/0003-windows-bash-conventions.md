---
id: 0003
slug: windows-bash-conventions
title: Windows git bash 用 /dev/null 與正斜線路徑
date: 2026-04-11
tags: [windows, shell]
---

## 錯誤是什麼

在 Windows 上把 git bash 當成 cmd / PowerShell 用：

- 寫 `2>NUL`（cmd 語法）→ bash 會當成檔名建立 `NUL` 檔
- 寫 `C:\Users\...` 反斜線路徑 → bash 把 `\U` 當跳脫序列
- 寫 `dir`、`type`、`findstr` 等 cmd 內建指令 → bash 沒這些指令

## 為什麼犯

AI 看到 `Platform: win32` 就切換成 Windows cmd 語法，忽略了使用者設定的 shell 其實是 **bash**
（git bash / MSYS2 / WSL-ish）。Windows ≠ cmd。

## 未來如何避免

1. **檢查 shell 而非 OS**：Claude Code 啟動訊息會標 `Shell: bash`，以此為準
2. **路徑一律正斜線**：`C:/Users/LOREN/...` 在 git bash 完全可讀
3. **重導向用 `/dev/null`**：`cmd 2>/dev/null`，不是 `2>NUL`
4. **指令用 POSIX**：`ls` 不是 `dir`、`cat` 不是 `type`、`grep` 不是 `findstr`
5. **環境變數用 `$VAR`**：不是 `%VAR%`

## 如何判斷是否適用

- 所有在 Windows 上透過 git bash 跑 bash 指令的情境
- 若未來使用者改用 PowerShell，此 lesson 不適用，要參考使用者設定
- Hook 腳本（.claude/hooks/*.sh）本身也要遵守此規則，因為它們也是 bash
