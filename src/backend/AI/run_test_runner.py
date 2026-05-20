import importlib.util
from pathlib import Path
import tempfile
import sys


def run_test():
    test_path = Path(__file__).resolve().parent / "test_cover_letter_generator.py"
    spec = importlib.util.spec_from_file_location("test_cover", str(test_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Create a temporary directory similar to pytest's tmp_path
    with tempfile.TemporaryDirectory() as td:
        # If the test function exists, call it
        if hasattr(mod, "test_generate_cover_letter_and_tex"):
            try:
                from pathlib import Path as _P
                mod.test_generate_cover_letter_and_tex(_P(td))
                print("TEST PASSED")
                return 0
            except AssertionError as e:
                print("TEST FAILED:", e)
                return 2
            except Exception as e:
                import logging
                logging.error("TEST ERROR: %s", e, exc_info=True)
                return 3
        else:
            print("No test function found")
            return 4


if __name__ == "__main__":
    rc = run_test()
    sys.exit(rc)
