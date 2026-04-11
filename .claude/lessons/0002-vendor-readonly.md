---
id: 0002
slug: vendor-readonly
title: vendor/ 是只讀目錄，客製化寫在 services 層
date: 2026-04-11
tags: [vendor, architecture]
---

## 錯誤是什麼

當 PHALP / 4D-Humans / smpl2bvh / bvh2vrma 的行為不符合需求時，直覺反應是「直接改 vendor 裡的檔案」。
這會造成：

- 升級 vendor 時衝突
- 他人 clone 後行為不一致（因為 patch 散在各處）
- git blame 混亂
- 上游 PR 也難以追蹤

## 為什麼犯

捷徑思維：看到 `vendor/PHALP/phalp/xxx.py` 第 N 行有問題，最短路徑就是直接改那行。
但「最短路徑」在工程上不等於「最好路徑」。

根因是把 vendor 當成「我們的程式碼」，忘記了它是第三方上游的凍結拷貝。

## 未來如何避免

1. **Python 客製化**：在 `backend/app/services/` 建 adapter，透過繼承 / composition / monkey-patch 在呼叫端修正
   ```python
   # backend/app/services/phalp_service.py
   from phalp.trackers.PHALP import PHALP as _UpstreamPHALP

   class PHALPAdapter(_UpstreamPHALP):
       def __init__(self, cfg):
           # 在呼叫 super 之前 patch 掉有問題的地方
           super().__init__(cfg)
   ```

2. **TypeScript 客製化**：在 `frontend/src/services/` 重寫或 re-export
   ```typescript
   // frontend/src/services/bvhToVrma.ts
   import { coreConvert } from '../../vendor/bvh2vrma/src/lib/bvh-converter';
   // 加我們的前後處理
   ```

3. **若上游真的有 bug**：開 issue 給上游，並在 services 層暫時 patch，留 TODO 註記預期的上游修法

4. **`.claude/hooks/block-vendor-write.sh` 會攔截**任何寫入 vendor/ 的操作，若被擋下就是訊號：改走 services 層

## 如何判斷是否適用

- 任何時候想改 `vendor/` 下的檔案
- 若 Hook 擋了你，不要試圖繞過，改走 adapter
- 唯一例外：使用者明確要求「手動合入上游 patch」並暫停 hook
