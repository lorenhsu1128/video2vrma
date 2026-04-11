---
description: 檢查 aicuda 環境與關鍵套件是否就緒
---

執行以下步驟：

1. 跑 `conda run -n aicuda python scripts/env_check.py`
2. 將輸出濃縮後回報：
   - Python / torch / CUDA 版本與 GPU 型號
   - 必要套件的 OK/FAIL 清單
   - vendor/ 各子專案 commit hash
   - 缺失套件（若有）及建議安裝方式
3. 若有 FAIL 的必要套件，**只給建議，不要自動安裝**（裝錯環境風險高，要使用者確認）
4. 若全部通過，簡短回報「環境 OK」即可
