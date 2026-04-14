# 0007 — PHALP 任何幀都可能沒有任何偵測

**Tags**: phalp, preview, robustness

## 錯誤是什麼

`backend/app/services/preview.py::render_overlay_video` 曾經用
`data[frame_keys[0]]["size"][0]` 取影片解析度，假設第一幀一定至少有一個偵測。
但 PHALP 對**任何**沒有人物的幀會回 `size=[]`（空 list），`[0]` 觸發 `IndexError: list index out of range`。

常見觸發情境：
- 影片**開頭**是 black intro / 字卡 / 風景鏡頭
- 影片**中段**某段時間人物離開畫面（轉場、空鏡、遮擋）
- 影片**結尾**人物已經走出畫面但影片還沒停

第一幀只是其中一種，不要以為「只處理前幾幀」就夠了。

commit `2680160` 修過另一個 IndexError（同函式內 tid/joints 長度不一致），容易讓人以為 overlay 的 IndexError 都已經修完 → 再犯時要記得還有「空偵測幀」這一類。

## 為什麼犯

- 直覺假設 PHALP 的每幀輸出都有內容（事實：PHALP 只是把影片每幀（或跳幀）都寫進 pkl，沒偵測到人就填空）。
- 前一個 IndexError 修好後沒有整個掃一遍還有哪裡在索引 PHALP 的 list。

## 未來如何避免

- 任何索引 PHALP per-frame list (`size` / `tid` / `2d_joints` / `smpl`) 前都要檢查非空，**不分幀在影片哪個位置**。
- 需要「任意可用幀」的資料（解析度、相機內參）時，掃 `frame_keys` 找第一個非空的，而不是直接 `frame_keys[0]`。
- 畫 overlay / 處理每幀的迴圈：`tids=[]`、`joints=[]` 時 inner loop 自然 skip，但別忘了也要能處理「整個影片前/中/後某段都空」的情況。
- 寫 defensive code 時順便搜一次同檔所有索引 PHALP list 的地方。

## 如何判斷適用

- 錯誤出現在 `preview.py`、`track_extractor.py` 或其他讀 PHALP pkl 的地方
- 訊息包含 `list index out of range` 並且發生在 `data[...][key][0]` 這類直接索引
- 影片有任何時段（開頭 / 中段 / 結尾）沒有人入鏡
