import importlib
from pathlib import Path


def load():
    for name in (p.stem for p in Path(__file__).parent.iterdir()):
        if not name.startswith("_"):
            importlib.import_module(f"{__package__}.{name}")
