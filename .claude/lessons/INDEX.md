# Lessons Index

此檔案會被 `CLAUDE.md` 透過 `@import` 自動載入，所以每次對話開始都看得到。
新增 lesson 時：建立 `NNNN-slug.md`，並在此加一行索引（依編號排序）。

## 條目

- [0001](0001-conda-run-multiline.md) — `conda run ... python -c` 不支援含換行字串，改寫成檔案（environment, windows, conda）
- [0002](0002-vendor-readonly.md) — `vendor/` 是只讀目錄，客製化寫在 services 層（vendor, architecture）
- [0003](0003-windows-bash-conventions.md) — Windows git bash 用 `/dev/null` 與正斜線路徑（windows, shell）
- [0004](0004-sm120-wheel-compatibility.md) — RTX 5070 Ti sm_120 對預編 wheel 相容性有限（cuda, environment）
- [0005](0005-vendor-import-side-effect-patches.md) — vendor/ 只讀時用 sys.modules stub + monkey-patch 繞過 import side-effect（vendor, architecture, windows）
- [0006](0006-phalp-bvh-vrm-coordinate-pipeline.md) — PHALP→BVH→VRMA→VRM 跨階段座標系與 rig 陷阱（coordinate, three-vrm, bvh2vrma, phase2）

## 規則摘要（取自所有 lessons）

- **Conda**：python 指令一律 `conda run -n aicuda ...`；多行程式碼寫成 .py 檔再跑
- **Vendor**：不得修改 `vendor/`；客製化寫在 `backend/app/services/` 或 `frontend/src/services/`
- **Shell**：Windows bash 用 `/dev/null`、正斜線路徑；不用 `NUL`、不用反斜線
- **CUDA/wheel**：sm_120 新架構，detectron2/pytorch3d 的預編 wheel 可能不支援，需考慮從原始碼編譯或改方案
- **座標系**：PHALP global_orient 是相機座標 (Y down, Z fwd)，要 `diag(1,-1,-1)` 轉到 VRM；VRM1 rest pose 面向 +Z 而 three.js 相機在 +Z 看 -Z，所以需 `rotation.y = Math.PI`；bvh2vrma 預設輸出的 hips position track 會把 VRM hips 拖到原點，要拿掉但保留 auto-grounding；VRM 載入後放 React state 不只 ref，`vrm.update(dt)` 必須每 frame 呼叫
