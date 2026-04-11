---
description: 自動完成一項功能（規劃→實作→測試→文件同步→commit），中途不詢問
---

使用者要你**端到端自動開發**一項功能，直到測試通過後自動 commit。
功能描述來自使用者的訊息參數：`$ARGUMENTS`

## 核心契約

- **中途不詢問**：不要每做一步就問使用者要不要繼續，直接走完整個流程
- **只在極端情況停下來**：定義見下方「何時該停下」
- **所有規則仍然生效**：CLAUDE.md、lessons、hooks 一律照跑，autodev 不是繞過它們的後門
- **只在測試真的通過後 commit**：不假裝、不跳過、不 `--no-verify`

## 執行流程

### 階段 1：規劃（內部思考，不輸出冗長內容）

1. 解析 `$ARGUMENTS` 理解要做什麼
2. 讀 `DEVELOPMENT_PLAN.md` 判斷這個功能屬於哪個 Phase、哪個任務編號
3. 用 Grep/Read 快速掃描會動到的檔案範圍
4. 心中列出：
   - 要新增/修改哪些檔案（**絕不含 vendor/**）
   - 測試策略（單元測試？e2e？手動驗證腳本？）
   - 是否需要更新 CLAUDE.md 目錄結構或 API 規格
5. 若規劃階段發現任務太大或太模糊 → 跳到「何時該停下」

### 階段 2：實作

1. 用 Edit / Write 實作所有變更
2. 遵守既有規範：
   - Python 指令一律 `conda run -n aicuda ...`
   - 不改 `vendor/`
   - 不加無謂的註解、不寫 docstring 長篇、不過度抽象
   - 不做超出當前任務的重構
3. 邊做邊在心中追蹤清單，完成一項劃掉一項
4. **不要中途報告進度**，保持安靜實作

### 階段 3：驗證

1. **靜態檢查**：若專案有 `ruff` / `mypy` / `tsc` / `eslint`，跑對應指令
2. **測試**：
   - 若有明確的單元測試檔，跑 `conda run -n aicuda pytest <path> -x`
   - 若是後端新模組，至少寫一個 smoke test 並跑過
   - 若是前端元件，至少 tsc 編譯通過
   - 若是 GPU pipeline 類任務（慢），跑最小重現案例而非完整 e2e
3. **失敗處理**：
   - 測試失敗 → 修 bug → 重跑（最多 **3 次**重試）
   - 3 次後仍失敗 → 跳到「何時該停下」
   - **不**用 try/except 吞錯誤繞過測試
   - **不**降低測試門檻讓它通過
4. **自我 review**：看 `git diff`，確認沒有：
   - 無關的修改（格式化整個檔案、改別的功能）
   - 被註解掉的舊程式碼
   - `console.log` / `print` 除錯殘留
   - `TODO` / `FIXME` 留在新程式碼中（除非真的是未來工作）

### 階段 4：文件同步

1. 執行 `/update-plan` 的邏輯：更新 `DEVELOPMENT_PLAN.md` 對應任務勾選
2. 若新增了模組、API、目錄，更新 `CLAUDE.md` 的「目錄結構」或「API 規格」段落
3. 若這次開發過程中使用者糾正了你某個系統性錯誤，執行 `/save-lesson` 的邏輯

### 階段 5：Commit

1. 執行 `git status` 與 `git diff --stat` 確認要 commit 的範圍
2. 拒絕 commit 的情況：
   - `data/smpl/`、`.env*`、`*.pem`、`*.key` 出現在 staged 檔案裡
   - `vendor/` 被修改（理論上 hook 已擋，保險起見再檢查）
3. 產生 commit message：
   - **一律繁體中文**（不是簡體、不是英文）
   - 第一行 ≤ 50 字，簡述做了什麼
   - 空一行後寫 2-4 行說明「為什麼」與「測試方式」
   - 技術名詞可保留英文原文
   - 範例：
     ```
     新增 PHALP adapter 並修正 NumPy 2.x 相容性

     在 backend/app/services/phalp_service.py 建立 PHALPAdapter，
     包裝 vendor/PHALP 的入口並 monkey-patch np.float 的使用。
     測試：pytest backend/tests/test_phalp_service.py 全數通過。
     ```
4. 使用 HEREDOC 傳 message（避免 escaping 問題）
5. 執行 commit：
   ```bash
   git add <specific files>  # 不用 git add -A
   git commit -m "$(cat <<'EOF'
   <繁體中文訊息>

   Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
   EOF
   )"
   ```
6. **不要 push**。push 是跨機器的動作，需要使用者明示才能做

### 階段 6：最終報告

對使用者輸出一段簡短總結（≤ 150 字），包含：

- ✅ 完成了什麼（一兩句）
- 📝 動了哪些檔案（列 path，不貼內容）
- 🧪 測試結果（哪幾個測試、是否通過）
- 📚 是否更新了 CLAUDE.md / DEVELOPMENT_PLAN.md / lessons
- 📦 Commit hash（`git rev-parse --short HEAD`）
- ⚠️ 需要使用者注意的後續事項（若有）

## 何時該停下（這些情況**停下來報告**，不要硬幹）

若碰到以下情形，**立即停止自動流程**，輸出現況並等使用者決策：

1. **任務描述模糊到無法規劃**：多種合理解讀、缺關鍵前提
2. **範圍遠超預期**：原本以為改 3 個檔案，實作時發現要動 30 個
3. **需要使用者才有的資源**：測試影片、API 金鑰、模型權重、手動驗證
4. **測試連續失敗 3 次仍未通過**：繼續嘗試只會亂改程式碼
5. **碰到需要修改 `vendor/` 才能解決的根本問題**：違反專案鐵則
6. **發現潛在破壞性操作**：DB migration、刪檔、改 CI、改權限
7. **發現機密外洩風險**：diff 中出現 token / 密碼 / 私鑰
8. **測試通過但 diff 包含超過任務範圍的修改**：可能做過頭了，請使用者確認

停下來時的報告格式：

```
⏸ 自動開發暫停

原因：<哪一項停下條件>
當前狀態：<已做 / 未做>
建議：<使用者可以怎麼決策>
未 commit 的變更：<file paths>
```

此時**不要** commit、**不要** revert、**不要**繼續猜測。

## 禁止事項（無論如何都不做）

- ❌ `git push`（哪怕只是 push 到 fork）
- ❌ `git reset --hard` / `git checkout .` / `git clean -f`
- ❌ `git rebase -i` / `git commit --amend`
- ❌ `--no-verify` 繞 pre-commit hook
- ❌ 跳過或刪除失敗的測試讓 CI 綠燈
- ❌ 修改 `.claude/settings.json` 停用 hooks
- ❌ 修改 `vendor/`
- ❌ 安裝新套件到 base 環境
- ❌ 刪除使用者追蹤中的檔案或分支
- ❌ 使用 `pip install --force` / `--ignore-requires-python` 硬裝套件
- ❌ 將 `data/smpl/` 或任何授權模型檔加入 git

## 範例呼叫

```
/auto-feature 實作 backend/app/services/phalp_service.py，包裝 vendor/PHALP 的最小推論路徑，輸出 SMPL 參數 dict，並寫一個 smoke test
```

```
/auto-feature 新增 FastAPI /api/upload 端點，接收 mp4 multipart 上傳存到 tmp/uploads/，回傳 task_id
```

---

**記住核心契約**：不詢問、不繞規則、不假通過、不過範圍。若四者衝突，選「停下來報告」。
