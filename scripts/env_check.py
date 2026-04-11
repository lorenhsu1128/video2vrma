"""video2vrma 環境檢查腳本。

使用方式：
    conda run -n aicuda python scripts/env_check.py

回報項目：
    - Python / torch / CUDA 版本與 GPU
    - 必要套件 OK/FAIL
    - vendor/ 子專案 import 是否可用
    - vendor/ 各子專案 commit hash
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

REQUIRED: list[str] = [
    "torch", "torchvision", "torchaudio",
    "pytorch_lightning", "hydra", "omegaconf",
    "transformers", "cv2", "mediapipe",
    "pyrender", "trimesh", "scipy", "numpy",
    "fastapi", "uvicorn", "websockets",
    "chumpy", "yacs",
]

OPTIONAL: list[str] = ["smplx", "pytorch3d", "detectron2", "multipart"]

VENDOR_SYS_PATH: list[str] = ["vendor/4d-humans", "vendor/PHALP"]
VENDOR_IMPORTS: list[str] = ["hmr2", "phalp"]


def check(mod: str) -> tuple[bool, str]:
    try:
        m = importlib.import_module(mod)
        v = getattr(m, "__version__", "?")
        return True, str(v)
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:60]}"


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    for p in VENDOR_SYS_PATH:
        sys.path.insert(0, str(root / p))

    print("=" * 60)
    print("video2vrma environment check")
    print("=" * 60)
    print(f"Python: {sys.version.split()[0]}")

    try:
        import torch  # type: ignore
        print(f"torch:  {torch.__version__}")
        cuda_ok = torch.cuda.is_available()
        print(f"CUDA:   available={cuda_ok}  version={torch.version.cuda}")
        if cuda_ok:
            print(f"Device: {torch.cuda.get_device_name(0)}  CC={torch.cuda.get_device_capability(0)}")
    except Exception as e:
        print(f"torch:  FAIL {e}")

    print("\n--- Required packages ---")
    fail: list[str] = []
    for m in REQUIRED:
        ok, info = check(m)
        mark = "OK  " if ok else "FAIL"
        print(f"  [{mark}] {m:22s} {info}")
        if not ok:
            fail.append(m)

    print("\n--- Vendor imports ---")
    for m in VENDOR_IMPORTS:
        ok, info = check(m)
        mark = "OK  " if ok else "FAIL"
        print(f"  [{mark}] {m:22s} {info}")
        if not ok:
            fail.append(m)

    print("\n--- Optional packages ---")
    for m in OPTIONAL:
        ok, info = check(m)
        mark = "OK  " if ok else "--  "
        print(f"  [{mark}] {m:22s} {info}")

    print("\n--- Vendor commit hashes ---")
    vendor_dir = root / "vendor"
    if vendor_dir.exists():
        for d in sorted(vendor_dir.iterdir()):
            if not d.is_dir():
                continue
            try:
                h = subprocess.check_output(
                    ["git", "rev-parse", "--short", "HEAD"],
                    cwd=d, text=True, stderr=subprocess.DEVNULL,
                ).strip()
            except Exception:
                h = "(not a git repo)"
            print(f"  {d.name:20s} {h}")
    else:
        print("  vendor/ not found")

    print()
    if fail:
        print(f"FAIL: {len(fail)} required package(s) missing: {', '.join(fail)}")
        return 1
    print("All required checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
