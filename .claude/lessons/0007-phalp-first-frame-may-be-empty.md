# 0007 — PHALP 第一幀可能沒有任何偵測

**Tags**: phalp, preview, robustness

## 錯誤是什麼

`backend/app/services/preview.py::render_overlay_video` 曾經用
`data[frame_keys[0]]["size"][0]` 取影片解析度，假設第一幀一定至少有一個偵測。
但 PHALP 在場景前幾幀沒有人出現時 `size=[]`（空 list），`[0]` 觸發 `IndexError: list index out of range`。

commit `2680160` 修過另一個 IndexError（同函式內 tid/joints 長度不一致），容易讓人以為 overlay 的 IndexError 都已經修完 → 再犯時要記得還有「第一幀空偵測」這一個。

## 為什麼犯

- 把 PHALP 的 `frame_keys[0]` 當作「一定有內容的幀」的直覺假設。
- 前一個 IndexError 修好後沒有整個掃一遍還有哪裡在索引 PHALP 的 list。

## 未來如何避免

- 任何索引 PHALP per-frame list (`size` / `tid` / `2d_joints` / `smpl`) 前都要檢查非空。
- 需要「任意可用幀」的資料（解析度、相機內參）時，掃 `frame_keys` 找第一個非空的，而不是直接 `frame_keys[0]`。
- 寫 defensive code 時順便搜一次同檔所有索引 PHALP list 的地方。

## 如何判斷適用

- 錯誤出現在 `preview.py`、`track_extractor.py` 或其他讀 PHALP pkl 的地方
- 訊息包含 `list index out of range` 並且發生在 `data[...][key][0]` 這類直接索引
- 影片前幾秒沒有人入鏡（black intro、風景鏡頭、字卡）
