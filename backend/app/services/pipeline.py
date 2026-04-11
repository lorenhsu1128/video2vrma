from pathlib import Path

from .phalp_service import run_phalp
from .smpl_to_bvh_service import convert_pkl_to_bvh
from .vendor_paths import ROOT


def run_e2e(
    video_path: str | Path,
    output_dir: str | Path,
    end_frame: int = 300,
    fps: int = 30,
) -> dict:
    video_path = Path(video_path).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    phalp_out = output_dir / "phalp"
    pkl_path = run_phalp(video_path, phalp_out, start_frame=0, end_frame=end_frame)

    bvh_path = output_dir / f"{video_path.stem}.bvh"
    convert_pkl_to_bvh(
        pkl_path=pkl_path,
        output_bvh=bvh_path,
        smpl_root=ROOT / "data" / "smpl",
        fps=fps,
    )
    return {"pkl": pkl_path, "bvh": bvh_path}
