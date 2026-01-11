"""
Pipeline Runner
Orchestrates the full data processing pipeline
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from importlib import import_module

def run_pipeline(data_dir="synthetic"):
    """
    Run the complete data processing pipeline

    Args:
        data_dir: Either "real" or "synthetic" (default: "synthetic" for safety)
    """
    print("=" * 60)
    print(f"RUNNING PIPELINE FOR {data_dir.upper()} DATA")
    print("=" * 60)

    steps = [
        ("01_load_anz", "load_and_process_anz", "Loading ANZ data"),
        ("02_load_bankwest", "load_and_process_bankwest", "Loading Bankwest data"),
        ("03_combine", "combine_transactions", "Combining transactions"),
        ("04_categorize", "categorize_transactions", "Categorizing transactions"),
    ]

    for module_name, func_name, description in steps:
        print(f"\n{'=' * 60}")
        print(f"STEP: {description}")
        print("=" * 60)

        module = import_module(module_name)
        func = getattr(module, func_name)
        result = func(data_dir)

        if result is None:
            print(f"\nPipeline failed at: {description}")
            return False

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"\nOutput files in: data/processed/{data_dir}/")
    return True


if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "synthetic"
    if data_dir not in ["real", "synthetic"]:
        print(f"Error: data_dir must be 'real' or 'synthetic', got '{data_dir}'")
        print("\nUsage: python scripts/run_pipeline.py [synthetic|real]")
        sys.exit(1)

    success = run_pipeline(data_dir)
    sys.exit(0 if success else 1)
