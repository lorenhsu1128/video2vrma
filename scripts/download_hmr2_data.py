import os
import sys
import tarfile
import urllib.request
from pathlib import Path

URL = "https://www.cs.utexas.edu/~pavlakos/4dhumans/hmr2_data.tar.gz"
CACHE = Path(os.environ.get("HOME", os.environ.get("USERPROFILE", ""))) / ".cache" / "4DHumans"
CACHE.mkdir(parents=True, exist_ok=True)
TARBALL = CACHE / "hmr2_data.tar.gz"


def main():
    print(f"Downloading {URL}")
    print(f"       -> {TARBALL}")

    def report(block_num, block_size, total_size):
        downloaded = block_num * block_size
        pct = downloaded / total_size * 100 if total_size > 0 else 0
        sys.stdout.write(f"\r  {downloaded/1e6:.1f}/{total_size/1e6:.1f} MB ({pct:.1f}%)")
        sys.stdout.flush()

    urllib.request.urlretrieve(URL, TARBALL, reporthook=report)
    print()
    print(f"  size={TARBALL.stat().st_size} bytes")

    print("Extracting...")
    with open(TARBALL, "rb") as f:
        magic = f.read(2)
    mode = "r:gz" if magic == b"\x1f\x8b" else "r:"
    print(f"  tar mode: {mode}")
    with tarfile.open(TARBALL, mode) as tar:
        tar.extractall(CACHE)
    print("Done")

    required = [
        CACHE / "logs/train/multiruns/hmr2/0/model_config.yaml",
        CACHE / "logs/train/multiruns/hmr2/0/checkpoints/epoch=35-step=1000000.ckpt",
    ]
    for p in required:
        print(f"  {'OK ' if p.exists() else 'MISS'} {p}")


if __name__ == "__main__":
    main()
