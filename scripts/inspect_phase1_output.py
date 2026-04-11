import sys
from pathlib import Path

import joblib

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from app.services.smpl_to_bvh_service import extract_longest_track

pkl = ROOT / "tmp" / "phase1" / "phalp" / "results" / "demo_dance.pkl"
bvh = ROOT / "tmp" / "phase1" / "dance.bvh"

data = joblib.load(pkl)
print(f"pkl frames: {len(data)}")
sample_key = next(iter(data))
sample = data[sample_key]
print(f"sample frame keys: {sorted(sample.keys())[:12]}")
print(f"sample tids: {sample.get('tid')}")
print(f"sample smpl count: {len(sample.get('smpl', []))}")

pose_aa, tid = extract_longest_track(pkl)
print(f"longest track tid={tid} frames={pose_aa.shape[0]} shape={pose_aa.shape}")
print(f"pose_aa abs-mean: {abs(pose_aa).mean():.4f}")

bvh_text = bvh.read_text(encoding="utf-8")
header_lines = bvh_text.splitlines()[:6]
print("BVH head:")
for line in header_lines:
    print("  " + line)
frame_count_line = [l for l in bvh_text.splitlines() if l.startswith("Frames:")]
print(frame_count_line[0] if frame_count_line else "(no Frames: line)")
