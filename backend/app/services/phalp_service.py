import importlib.util
import logging
import os
import pickle
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

from . import vendor_paths  # noqa: F401  (side-effect: sys.path + HOME + stubs)

ROOT = vendor_paths.ROOT
_DEMO_PY = vendor_paths.VENDOR / "PHALP" / "scripts" / "demo.py"

log = logging.getLogger(__name__)

_cached_phalp_demo = None
_cached_tracker = None


def _load_phalp_demo():
    global _cached_phalp_demo
    if _cached_phalp_demo is not None:
        return _cached_phalp_demo
    spec = importlib.util.spec_from_file_location("phalp_demo", _DEMO_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _cached_phalp_demo = module
    return module


def _patch_hmr2_skip_renderer() -> None:
    import hmr2.models.hmr2 as _hmr2_mod

    if getattr(_hmr2_mod.HMR2.__init__, "_v2v_patched", False):
        return

    _orig_init = _hmr2_mod.HMR2.__init__

    def _patched_init(self, cfg, init_renderer: bool = False):
        _orig_init(self, cfg, init_renderer=False)

    _patched_init._v2v_patched = True  # type: ignore[attr-defined]
    _hmr2_mod.HMR2.__init__ = _patched_init


def _convert_py2_smpl_to_py3(src: Path, dst: Path) -> None:
    import dill  # noqa: F401
    try:
        dill._dill._reverse_typemap["ObjectType"] = object  # type: ignore[attr-defined]
    except Exception:
        pass
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(src, "rb") as f:
        loaded = pickle.load(f, encoding="latin1")
    with open(dst, "wb") as f:
        pickle.dump(loaded, f)


def _prepopulate_smpl_caches() -> None:
    src = ROOT / "data" / "smpl" / "basicmodel_neutral_lbs_10_207_0_v1.1.0.pkl"
    if not src.exists():
        raise FileNotFoundError(
            f"SMPL neutral model not found at {src}; cannot pre-populate caches"
        )

    home = Path(os.environ["HOME"])
    targets = [
        home / ".cache" / "phalp" / "3D" / "models" / "smpl" / "SMPL_NEUTRAL.pkl",
        home / ".cache" / "4DHumans" / "data" / "smpl" / "SMPL_NEUTRAL.pkl",
    ]
    for target in targets:
        if not target.exists():
            _convert_py2_smpl_to_py3(src, target)


@contextmanager
def _patch_tqdm_progress(cb: Callable[[float], None] | None):
    """在 with 區塊內 proxy tqdm.auto.tqdm，每次 update 用 n/total 回報給 cb。

    PHALP vendor 內部以 tqdm.auto.tqdm 顯示每幀進度；若未來 vendor 升級改用
    別的進度套件，此 patch 會悄悄失效（cb 不會被呼叫），但不會壞。
    """
    if cb is None:
        yield
        return
    try:
        import tqdm.auto as _ta
    except Exception:
        yield
        return

    orig = _ta.tqdm

    class _Proxy(orig):  # type: ignore[misc, valid-type]
        def update(self, n=1):
            r = super().update(n)
            try:
                if self.total:
                    cb(min(self.n / self.total, 1.0))
            except Exception:
                pass
            return r

    _ta.tqdm = _Proxy
    try:
        yield
    finally:
        _ta.tqdm = orig


def resolve_phalp_frame_range(
    start_frame: int | None = None,
    end_frame: int | None = None,
) -> tuple[int, int]:
    start = -1 if (start_frame is None or start_frame <= 0) else start_frame
    end = -1 if (end_frame is None or end_frame < 0) else end_frame
    return start, end


def run_phalp(
    video_path: str | Path,
    output_dir: str | Path,
    start_frame: int = -1,
    end_frame: int = -1,
    every_x_frame: int = 1,
    progress_cb: Callable[[float], None] | None = None,
) -> Path:
    global _cached_tracker

    video_path = Path(video_path).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    from .vendor_paths import set_every_x_frame
    set_every_x_frame(every_x_frame)

    _prepopulate_smpl_caches()
    phalp_demo = _load_phalp_demo()
    _patch_hmr2_skip_renderer()

    vid_start, vid_end = resolve_phalp_frame_range(start_frame, end_frame)

    if _cached_tracker is None:
        from omegaconf import OmegaConf
        cfg = OmegaConf.structured(phalp_demo.Human4DConfig())
        cfg.video.source = video_path.as_posix()
        cfg.video.output_dir = output_dir.as_posix()
        cfg.video.base_path = video_path.parent.as_posix()
        cfg.video.extract_video = True
        cfg.video.start_frame = vid_start
        cfg.video.end_frame = vid_end
        cfg.phalp.start_frame = -1
        cfg.phalp.end_frame = -1
        cfg.render.enable = False
        cfg.overwrite = False
        cfg.post_process.apply_smoothing = False
        cfg.detect_shots = False

        log.info("creating PHALP tracker (first run, loading GPU models)...")
        _cached_tracker = phalp_demo.HMR2_4dhuman(cfg)
        log.info("PHALP tracker created and cached")
    else:
        log.info("reusing cached PHALP tracker")
        cfg = _cached_tracker.cfg
        cfg.video.source = video_path.as_posix()
        cfg.video.output_dir = output_dir.as_posix()
        cfg.video.base_path = video_path.parent.as_posix()
        cfg.video.extract_video = True
        cfg.video.start_frame = vid_start
        cfg.video.end_frame = vid_end
        cfg.phalp.start_frame = -1
        cfg.phalp.end_frame = -1
        cfg.overwrite = False

    from .preview import _throttled
    throttled_cb = _throttled(progress_cb) if progress_cb else None
    with _patch_tqdm_progress(throttled_cb):
        _cached_tracker.track()

    video_seq = Path(video_path).stem
    pkl_path = output_dir / "results" / f"demo_{video_seq}.pkl"
    if not pkl_path.exists():
        raise FileNotFoundError(f"PHALP did not produce expected pkl at {pkl_path}")
    return pkl_path
