import importlib
from pathlib import Path


def load():
    for name in (p.stem for p in Path(__file__).parent.iterdir()):
        if name.startswith("_"):
            continue

        importlib.import_module(f"{__package__}.{name}")
