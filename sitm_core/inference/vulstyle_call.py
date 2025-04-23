import sys
import os
from sitm_core.utils.config import config
from sitm_core.inference.vulstyle import VulDetector

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    model_path = str(config.vulstyle_model_path)
    detector = VulDetector(model_path)
    paths = sys.argv[1:]
    blocked = False

    for path in paths:
        abs_path = os.path.abspath(path)
        filename = os.path.basename(abs_path)
        is_temp_remote = filename.startswith(".sitm_tmp_remote_")

        if detector.has_vulnerability(abs_path):
            if not is_temp_remote:
                print(f"⚠️  Detected vulnerability in {abs_path}.")
            blocked = True
            
    sys.exit(1 if blocked else 0)

if __name__ == "__main__":
    main()
