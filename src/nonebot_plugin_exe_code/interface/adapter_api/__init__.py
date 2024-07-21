import importlib
from pathlib import Path

modules = [
    importlib.import_module(f"{__package__}.{path.stem}")
    for path in Path(__file__).parent.iterdir()
    if not path.stem.startswith("_")
]
