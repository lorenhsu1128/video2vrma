import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor" / "4d-humans"))
sys.path.insert(0, str(ROOT / "vendor" / "PHALP"))

failures = []

def check(name, fn):
    try:
        result = fn()
        print(f"OK  {name}: {result}")
    except Exception as e:
        print(f"FAIL {name}: {type(e).__name__}: {e}")
        failures.append(name)

def _smplx():
    import smplx
    return smplx.__version__ if hasattr(smplx, "__version__") else "imported"

def _hmr2():
    import hmr2
    return "imported"

def _phalp():
    import phalp
    return "imported"

def _torch_cuda():
    import torch
    assert torch.cuda.is_available(), "CUDA not available"
    return f"{torch.__version__} cuda={torch.version.cuda} device={torch.cuda.get_device_name(0)}"

def _fastapi_multipart():
    import fastapi, uvicorn, multipart, websockets, scipy
    return f"fastapi={fastapi.__version__} multipart={multipart.__version__}"

check("torch+cuda", _torch_cuda)
check("smplx", _smplx)
check("hmr2", _hmr2)
check("phalp", _phalp)
check("fastapi stack", _fastapi_multipart)

if failures:
    print(f"\n{len(failures)} FAILED: {failures}")
    sys.exit(1)
print("\nAll Phase 0 core checks passed.")
