# Lessons Index

此檔案會被 `CLAUDE.md` 透過 `@import` 自動載入，所以每次對話開始都看得到。
新增 lesson 時：建立 `NNNN-slug.md`，並在此加一行索引（依編號排序）。

## 條目

- [0001](0001-conda-run-multiline.md) — `conda run ... python -c` 不支援含換行字串，改寫成檔案（environment, windows, conda）
- [0002](0002-vendor-readonly.md) — `vendor/` 是只讀目錄，客製化寫在 services 層（vendor, architecture）
- [0003](0003-windows-bash-conventions.md) — Windows git bash 用 `/dev/null` 與正斜線路徑（windows, shell）
- [0004](0004-sm120-wheel-compatibility.md) — RTX 5070 Ti sm_120 對預編 wheel 相容性有限（cuda, environment）

## 規則摘要（取自所有 lessons）

- **Conda**：python 指令一律 `conda run -n aicuda ...`；多行程式碼寫成 .py 檔再跑
- **Vendor**：不得修改 `vendor/`；客製化寫在 `backend/app/services/` 或 `frontend/src/services/`
- **Shell**：Windows bash 用 `/dev/null`、正斜線路徑；不用 `NUL`、不用反斜線
- **CUDA/wheel**：sm_120 新架構，detectron2/pytorch3d 的預編 wheel 可能不支援，需考慮從原始碼編譯或改方案
