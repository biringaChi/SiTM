import argparse
import os
from sitm_core.inference import InferenceVul, VulDetector
from sitm_core.cache.cache import save_cache

"""
Author: Chidera Biringa
"""

def main():
    parser = argparse.ArgumentParser(description="SiTM Scanner CLI")
    parser.add_argument("path", help="File or directory to scan")
    parser.add_argument("-cred", action="store_true", help="Run credential detection")
    parser.add_argument("-func", action="store_true", help="Run function-level vulnerability detection")
    parser.add_argument("--no-cache", action="store_true", help="Force full scan (bypass fast scan)")
    parser.add_argument("--reset-cache", action="store_true", help="Clear cache before scanning (only used with fast scan)")

    args = parser.parse_args()
    abs_path = os.path.abspath(args.path)

    if args.func:
        model_path = os.path.join(os.path.dirname(__file__), "..", "models", "bigvul")
        detector = VulDetector(model_path)

        if args.no_cache:
            detector.run_detection(abs_path)
        else:
            if args.reset_cache:
                save_cache({})
            detector.fast_scan(abs_path)

    elif args.cred:
        model_path = os.path.join(os.path.dirname(__file__), "..", "models", "dance", "m2.pth")
        detector = InferenceVul(model_path)

        if args.no_cache:
            detector.scan(abs_path)
        else:
            if args.reset_cache:
                save_cache({})
            detector.fast_scan(abs_path)

    else:
        print("You must specify either -cred or -func.")
        exit(1)