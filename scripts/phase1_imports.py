import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.services import vendor_paths  # noqa
from app.services.phalp_service import run_phalp  # noqa
from app.services.smpl_to_bvh_service import convert_pkl_to_bvh, extract_longest_track  # noqa
from app.services.pipeline import run_e2e  # noqa

print("All Phase 1 imports OK")
print("ROOT:", vendor_paths.ROOT)
