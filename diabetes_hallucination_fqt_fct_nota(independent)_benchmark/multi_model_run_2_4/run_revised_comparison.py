"""Run the revised horizontal comparison generator."""
import importlib.util
from pathlib import Path

script_dir = Path(__file__).resolve().parent
# Target: generate_300q_horizontal_comparison_修正.py (exclude generate_300q_horizontal_comparison.py)
revised_path = script_dir / "generate_300q_horizontal_comparison_修正.py"
if not revised_path.exists():
    raise FileNotFoundError("generate_300q_horizontal_comparison_修正.py not found")

spec = importlib.util.spec_from_file_location("gen_revised", str(revised_path))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.main()
