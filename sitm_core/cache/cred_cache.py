import hashlib
import json
from pathlib import Path

cache_file = Path(".sitm/cred_cache.json")

def normalize_line(line):
    return line.strip()

def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()

def get_file_line_hashes(file_path: str):
    try:
        with open(file_path, "r", errors = "ignore") as f:
            lines = f.readlines()
        normalized_lines = [normalize_line(line) for line in lines]
        return {
            "file_hash": compute_hash("".join(normalized_lines)),
            "line_hashes": {str(i): compute_hash(l) for i, l in enumerate(normalized_lines)},
            "lines": normalized_lines
        }
    except Exception as e:
        return {"error": str(e)}

def load_cache():
    if not cache_file.exists():
        return {}
    with open(cache_file, 'r') as f:
        return json.load(f)

def save_cache(data):
    cache_file.parent.mkdir(parents = True, exist_ok = True)
    with open(cache_file, "w") as f:
        json.dump(data, f, indent = 2)

def should_rescan(file_path: str, current_hashes: dict, cache_data: dict):
    cached = cache_data.get(file_path)
    if not cached:
        return True, list(current_hashes["line_hashes"].keys())
    if current_hashes["file_hash"] == cached.get("file_hash"):
        return False, []
    changed_lines = []
    for i, hash_now in current_hashes["line_hashes"].items():
        prev_hash = cached["line_hashes"].get(i)
        if prev_hash != hash_now:
            changed_lines.append(i)
    vulnerable_lines = cached.get("vulnerable_lines", {})
    unchanged_vuln_lines = all(
        i not in changed_lines for i in vulnerable_lines.keys()
    )
    if unchanged_vuln_lines and changed_lines:
        return False, []
    return True, changed_lines