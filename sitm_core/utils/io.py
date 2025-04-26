import os
from typing import List

"""
Author: Chidera Biringa
"""

def is_text_file(file_path: str) -> bool:
    try:
        with open(file_path, "rb") as f:
            return b"\0" not in f.read(1024)
    except Exception as e:
        print(f"Skipping unreadable file: {file_path} — {e}")
        return False

def get_all_text_files(path: str | List[str]) -> List[str]:
    files: List[str] = []
    paths = path if isinstance(path, list) else [path]

    for p in paths:
        if os.path.isfile(p) and is_text_file(p):
            files.append(p)
        elif os.path.isdir(p):
            for root, _, filenames in os.walk(p):
                for name in filenames:
                    full_path = os.path.join(root, name)
                    if is_text_file(full_path):
                        files.append(full_path)
    return files

def read_file_lines(file_path: str) -> List[str]:
    try:
        with open(file_path, "r") as f:
            return f.readlines()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

def read_source_code(file_path: str) -> str:
    try:
        with open(file_path, "r") as f:
            return f.read()
    except Exception as e:
        print(f"Failed to read {file_path}: {e}")
        return ""