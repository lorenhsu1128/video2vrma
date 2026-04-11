import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VENDOR = ROOT / "vendor"

if "HOME" not in os.environ:
    os.environ["HOME"] = os.environ.get("USERPROFILE", str(Path.home()))

_PATHS = [
    VENDOR / "PHALP",
    VENDOR / "4d-humans",
    VENDOR / "smpl2bvh",
]

for p in _PATHS:
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)


class _PyrenderNoop:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return _PyrenderNoop()

    def __getattr__(self, name):
        return _PyrenderNoop()


def _stub_pyrender() -> None:
    # Windows 沒有 libEGL，pyrender / OpenGL 在 import 時會炸。
    # Phase 1 不需要 render，用 permissive 的 stub 把 pyrender 整個蓋掉，
    # 讓 hmr2 / phalp 內凡是 `import pyrender` 都直接綁到 stub。
    if "pyrender" in sys.modules:
        return
    stub = types.ModuleType("pyrender")
    stub.__file__ = "<v2v pyrender stub>"
    stub.__path__ = []  # type: ignore[attr-defined]

    def _getattr(name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _PyrenderNoop

    stub.__getattr__ = _getattr  # type: ignore[attr-defined]
    sys.modules["pyrender"] = stub


def _stub_phalp_renderer() -> None:
    # PHALP 的 phalp.visualize.py_renderer 也會強制 EGL，同樣攔截。
    key = "phalp.visualize.py_renderer"
    if key in sys.modules:
        return
    stub = types.ModuleType(key)
    stub.Renderer = _PyrenderNoop
    sys.modules[key] = stub


def _stub_neural_renderer() -> None:
    # neural_renderer 是過時套件，Windows 沒 wheel。
    # PHALP 的 HMR2023TextureSampler 只用它算 UV texture 的 depth visibility。
    # Phase 1 只需要 SMPL 參數（from model_out['pred_smpl_params']），
    # uv_image 不會被我們消費，depth 回傳一個巨大常數讓 visibility mask 全部為 True 即可。
    if "neural_renderer" in sys.modules:
        return
    stub = types.ModuleType("neural_renderer")
    stub.__file__ = "<v2v neural_renderer stub>"

    class _NRRenderer:
        def __init__(self, **kwargs):
            self.image_size = kwargs.get("image_size", 256)

        def __call__(self, vertices, faces, mode="depth", K=None, R=None, t=None, **kwargs):
            import torch

            b = vertices.shape[0]
            h = w = self.image_size
            return torch.full((b, h, w), 1e6, dtype=vertices.dtype, device=vertices.device)

    stub.Renderer = _NRRenderer
    sys.modules["neural_renderer"] = stub


def _patch_torch_load_weights_only() -> None:
    # PyTorch 2.6+ 預設 torch.load(weights_only=True)，會擋掉含
    # omegaconf.DictConfig 的 Lightning checkpoint（4D-Humans 就是）。
    # 我們在 local trusted 環境下，把預設回到 False。
    import torch

    if getattr(torch.load, "_v2v_patched", False):
        return
    _orig = torch.load

    def _patched(*args, **kwargs):
        kwargs.setdefault("weights_only", False)
        return _orig(*args, **kwargs)

    _patched._v2v_patched = True  # type: ignore[attr-defined]
    torch.load = _patched


_stub_pyrender()
_stub_phalp_renderer()
_stub_neural_renderer()
_patch_torch_load_weights_only()
