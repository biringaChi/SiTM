import os
import platform
from clang import cindex

"""
Author: Chidera Biringa
"""

def configure_clang():
    if cindex.Config.loaded:
        return

    env_path = os.getenv("LIBCLANG_PATH")
    if env_path:
        try:
            cindex.Config.set_library_file(env_path)
            return
        except Exception:
            pass

    fallback_paths = {
        "Darwin": [
            "/usr/local/opt/llvm/lib/libclang.dylib",
            "/opt/homebrew/opt/llvm/lib/libclang.dylib",
            "/Library/Developer/CommandLineTools/usr/lib/libclang.dylib",
        ],
        "Linux": [
            "/usr/lib/llvm-14/lib/libclang.so",
            "/usr/lib/x86_64-linux-gnu/libclang.so",
            "/usr/local/lib/libclang.so",
        ],
        "Windows": [
            "C:\\Program Files\\LLVM\\bin\\libclang.dll",
            "C:\\Program Files (x86)\\LLVM\\bin\\libclang.dll",
        ],
    }

    system = platform.system()
    for path in fallback_paths.get(system, []):
        if os.path.exists(path):
            try:
                cindex.Config.set_library_file(path)
                return
            except Exception:
                continue

    raise RuntimeError("Could not locate libclang. Install LLVM or set LIBCLANG_PATH.")
