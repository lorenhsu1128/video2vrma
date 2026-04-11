import importlib

pkgs = ["multipart", "smplx", "pytorch3d", "detectron2"]
for name in pkgs:
    try:
        m = importlib.import_module(name)
        ver = getattr(m, "__version__", "?")
        print(f"OK  {name} {ver}")
    except Exception as e:
        print(f"MISSING {name}: {type(e).__name__}: {e}")
