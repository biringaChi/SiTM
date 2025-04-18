import sys
import os
from sitm.inference import InferenceVul

def main():
    if len(sys.argv) < 2:
        # log output for no args
        sys.exit(1)

    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "dance", "m2.pth"))
    detector = InferenceVul(model_path)

    paths = sys.argv[1:]
    blocked = False

    for path in paths:
        abs_path = os.path.abspath(path)
        if detector.has_credentials(abs_path):
            print(f"⚠️  Detected vulnerability in {abs_path}.")
            blocked = True

    if blocked:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
