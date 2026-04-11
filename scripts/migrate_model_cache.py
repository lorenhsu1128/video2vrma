import os
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
PROJECT_HOME = MODELS_DIR / "_home"
PROJECT_IOPATH = MODELS_DIR / "iopath_cache"

USER_HOME = Path(os.environ.get("USERPROFILE", os.environ.get("HOME", "")))

MOVES = [
    (USER_HOME / ".cache" / "phalp", PROJECT_HOME / ".cache" / "phalp"),
    (USER_HOME / ".cache" / "4DHumans", PROJECT_HOME / ".cache" / "4DHumans"),
    (USER_HOME / ".torch" / "iopath_cache", PROJECT_IOPATH),
]


def du(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for dirpath, _, files in os.walk(path):
        for f in files:
            try:
                total += (Path(dirpath) / f).stat().st_size
            except OSError:
                pass
    return total


def main():
    PROJECT_HOME.mkdir(parents=True, exist_ok=True)
    PROJECT_IOPATH.mkdir(parents=True, exist_ok=True)

    for src, dst in MOVES:
        print(f"\n[{src.name}]")
        print(f"  src: {src}")
        print(f"  dst: {dst}")
        if not src.exists():
            print("  SKIP (source missing)")
            continue
        if dst.exists() and any(dst.iterdir()):
            print(f"  SKIP (dest already populated, {du(dst)/1e9:.2f} GB)")
            continue
        size = du(src)
        print(f"  moving {size/1e9:.2f} GB...")
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            dst.rmdir()
        shutil.move(str(src), str(dst))
        print("  OK")

    # Cleanup: if hmr2_data.tar.gz still sits in moved 4DHumans dir, it's only needed
    # for first-time extraction. Keep it? 2.7GB redundant; delete to save space.
    redundant = PROJECT_HOME / ".cache" / "4DHumans" / "hmr2_data.tar.gz"
    extracted_flag = PROJECT_HOME / ".cache" / "4DHumans" / "logs" / "train" / "multiruns" / "hmr2" / "0" / "model_config.yaml"
    if redundant.exists() and extracted_flag.exists():
        size_gb = redundant.stat().st_size / 1e9
        print(f"\nRemoving redundant tarball ({size_gb:.2f} GB): {redundant}")
        redundant.unlink()

    print("\nFinal layout:")
    for p in [PROJECT_HOME, PROJECT_IOPATH]:
        print(f"  {p} = {du(p)/1e9:.2f} GB")


if __name__ == "__main__":
    main()
