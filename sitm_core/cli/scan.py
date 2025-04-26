import argparse
import os
from sitm_core.cache.cache import save_cache
from sitm_core.utils.config import config
from sitm_core.inference import FastCredentialInference, FastVulnerabilityInference

"""
Author: Chidera Biringa
"""

def main():
    parser = argparse.ArgumentParser(description = "sitm scanner cli")
    parser.add_argument("path", help = "file or directory to scan")
    parser.add_argument("-cred", action = "store_true", help = "run credential detection")
    parser.add_argument("-func", action = "store_true", help = "run function-level vulnerability detection")
    parser.add_argument("--no-cache", action = "store_true", help = "force full scan (bypass fast scan)")
    parser.add_argument("--reset-cache", action = "store_true", help = "clear cache before scanning (only used with fast scan)")

    args = parser.parse_args()
    abs_path = os.path.abspath(args.path)

    if args.func:
        model_path = str(config.vulstyle_model_path)
        detector = FastVulnerabilityInference(model_path)
        if args.no_cache:
            detector.scan(abs_path)
        else:
            if args.reset_cache:
                save_cache({})
            detector.fast_scan(abs_path)
    elif args.cred:
        model_path = str(config.dance_model_path)
        detector = FastCredentialInference(model_path)
        if args.no_cache:
            detector.scan(abs_path)
        else:
            if args.reset_cache:
                save_cache({})
            detector.fast_scan(abs_path)
    else:
        print("you must specify either -cred or -func.")
        exit(1)