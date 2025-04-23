import argparse
import os
from sitm_core.inference import InferenceVul, VulDetector

def main():
    parser = argparse.ArgumentParser(description = "SiTM Scanner CLI")
    parser.add_argument("path", help = "File or directory to scan")
    parser.add_argument("-cred", action = "store_true", help = "Run credential detection")
    parser.add_argument("-func", action = "store_true", help = "Run function-level vulnerability detection")

    args = parser.parse_args()
    abs_path = os.path.abspath(args.path)

    if args.cred:
        model_path = os.path.join(os.path.dirname(__file__), "..", "models", "dance", "m2.pth")
        detector = InferenceVul(model_path)
        detector.run_detection(abs_path)
    elif args.func:
        model_path = os.path.join(os.path.dirname(__file__), "..", "models", "bigvul")
        detector = VulDetector(model_path)
        detector.run_detection(abs_path)
    else:
        print("❌ You must specify either -cred or -func")
        exit(1)
