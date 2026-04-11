---
id: 0005
slug: vendor-import-side-effect-patches
title: vendor/ 只讀時，用 sys.modules stub + monkey-patch 處理 import side-effect
date: 2026-04-11
tags: [vendor, architecture, windows, import]
---

## 錯誤是什麼

直接 `import` vendor/PHALP 與 vendor/4d-humans 在 Windows + Py3.12 + torch 2.7 會連續踩地雷：

- `pyrender` 在 __init__ 時強制 `PYOPENGL_PLATFORM=egl` → Windows 沒 `libEGL.dll` 載入失敗
- `vendor/PHALP/phalp/visualize/py_renderer.py` 與 `vendor/4d-humans/hmr2/utils/renderer.py` 都在 module 頂層 `import pyrender`，連 `cfg.render.enable=False` 也救不了
- `neural_renderer` 是早已棄用的套件，Windows 完全沒 wheel
- `hmr2.models.hmr2.HMR2.__init__` 預設 `init_renderer=True`，Lightning `load_from_checkpoint` 重建模型時會實例化 `SkeletonRenderer` / `MeshRenderer`，真的會呼叫 `pyrender.OffscreenRenderer()`
- PyTorch 2.6+ 預設 `torch.load(weights_only=True)` 擋掉含 `omegaconf.DictConfig` 的 Lightning checkpoint
- PHALP.cached_download_from_drive 用 `os.system("wget ...")`，Windows 沒 wget
- PHALP 的 `phalp.utils.io.get_frames_from_source` 用 `source_path.split('/')[-1]` 抽 video_name，Windows 反斜線路徑會炸
- 4D-Humans 的 `hmr2_data.tar.gz` URL 實際是未壓縮 tar，Python `tarfile.open(r:gz)` 會炸

## 為什麼犯

1. 只看 `cfg.render.enable=False` 就以為 render 鏈路可以完全不走，但 `import pyrender` 發生在 class definition / module load 時機，早於 cfg 生效
2. vendor 是只讀原則，但「只讀」不代表「不能攔截載入」——Python 的 `sys.modules` 與 monkey-patch 可以在不改檔案的前提下改變行為
3. 忽略了作業系統差異：vendor 原作者在 Linux 上跑，shell 指令（wget / tar -xzf）、路徑分隔符、compute capability 全都沒問題，Windows 一個個都是雷

## 未來如何避免

1. **vendor 的 import chain 有地雷時，用 sys.modules stub 攔截**：
   ```python
   stub = types.ModuleType("pyrender")
   stub.__file__ = "<stub>"         # 必須設，不然 inspect 會炸
   stub.__path__ = []
   stub.__getattr__ = lambda n: (...)  # 只處理非 dunder，dunder 要 AttributeError
   sys.modules["pyrender"] = stub
   ```
2. **第三方 class 的預設參數有地雷時，用 monkey-patch**：
   ```python
   _orig = Cls.__init__
   def _patched(self, x, y=False):  # signature 要跟原來一致，否則 Lightning 的 save_hyperparameters 內省會炸
       _orig(self, x, y=False)
   Cls.__init__ = _patched
   ```
3. **vendor 預期的 cache 檔案可以預填**：不要依賴 vendor 的 shell-based 下載，用 Python `urllib` / `tarfile` 自己先下好、放對位置、轉好格式
4. **側作用集中管理**：所有這類 patch 放在 `backend/app/services/vendor_paths.py` 的 module-level，由任何 service 第一次 `from . import vendor_paths` 時觸發
5. **Windows 絕對路徑給 vendor 時用 `Path.as_posix()`**：許多套件硬寫 `/` 分隔符
6. **`torch.load` 的 weights_only 政策**：在 local trusted 環境下 patch 預設為 False；production 環境應該用 `torch.serialization.add_safe_globals([...])` 白名單化

## 如何判斷是否適用

- 任何時候 vendor/ 被要求只讀，但 vendor 本身的 import chain 在我們的環境下跑不起來
- 任何時候第三方 class 的預設行為在我們的環境下會產生不必要的副作用（renderer、plot、log 外洩）
- 任何時候 vendor 的 shell-based 下載／解壓腳本依賴 Linux 指令
