import os
import torch
from typing import List, Union
from transformers import logging
from simpletransformers.classification import ClassificationModel
from sitm_core.cache.cache import load_cache, save_cache, hash_c_function
from sitm_core.utils.functions import get_all_c_files, parse_c_file, view_results_func

logging.set_verbosity_error()

"""
Author: Chidera Biringa
"""

class VulnerabilityInference:
    def __init__(self, model_dir: str):
        self.model_dir = model_dir

    def _get_model(self) -> ClassificationModel:
        cpu_total = os.cpu_count()
        parallelism = max(1, cpu_total // 2)
        model = ClassificationModel(
            "roberta",
            self.model_dir,
            use_cuda = torch.cuda.is_available(),
            args = {
                "process_count": parallelism,
                "use_multiprocessing": True,
                "silent": True
            }
        )
        return model

    def scan(self, path: Union[str, List[str]]) -> None:
        files = get_all_c_files(path)
        if not files:
            print("No C/C++ files found.")
            return
        model = self._get_model()
        for file_path in files:
            try:
                extracted = parse_c_file(file_path)
                if not extracted:
                    print(f"Skipping: No functions found in {file_path}")
                    continue
                func_names, func_bodies = zip(*extracted)
                predictions, _ = model.predict(list(func_bodies))
                view_results_func(file_path, func_names, func_bodies, predictions, verbose=True)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue

    def has_vulnerability(self, path: Union[str, List[str]]) -> bool:
        files = get_all_c_files(path)
        if not files:
            return False
        model = self._get_model()
        for file_path in files:
            try:
                extracted = parse_c_file(file_path)
                if not extracted:
                    continue
                _, func_bodies = zip(*extracted)
                predictions, _ = model.predict(list(func_bodies))
                if any(pred == 1 for pred in predictions):
                    return True
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
                continue
        return False


class FastVulnerabilityInference(VulnerabilityInference):
    def fast_scan(self, path: Union[str, List[str]]) -> None:
        files = get_all_c_files(path)
        if not files:
            print("No C/C++ files found.")
            return
        model = self._get_model()
        cache = load_cache()
        for file_path in files:
            try:
                extracted = parse_c_file(file_path)
                if not extracted:
                    print(f"Skipping: No functions found in {file_path}")
                    continue
                current_func_hashes = {name: hash_c_function(body) for name, body in extracted}
                cached = cache.get(file_path, {})
                cached_hashes = cached.get("func_hashes", {})
                vuln_funcs = cached.get("vulnerable_funcs", {})
                changed_funcs = {name: body for name, body in extracted if current_func_hashes.get(name) != cached_hashes.get(name)}
                new_predictions = {}
                if changed_funcs:
                    preds, _ = model.predict(list(changed_funcs.values()))
                    new_predictions = {name: {"prediction": int(pred), "body": changed_funcs[name]} for name, pred in zip(changed_funcs.keys(), preds) if pred == 1}
                final_vuln_funcs = {**{k: v for k, v in vuln_funcs.items() if k not in changed_funcs}, **new_predictions}
                if final_vuln_funcs:
                    func_names = list(final_vuln_funcs.keys())
                    func_bodies = [final_vuln_funcs[name]["body"] for name in func_names]
                    predictions = [1] * len(func_names)
                    view_results_func(file_path, func_names, func_bodies, predictions, verbose=True)
                else:
                    print(f"No vulnerabilities found in {file_path}.")
                cache[file_path] = {"func_hashes": current_func_hashes, "vulnerable_funcs": final_vuln_funcs}
                save_cache(cache)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue

    def fast_has_vulnerability(self, path: Union[str, List[str]]) -> bool:
        files = get_all_c_files(path)
        if not files:
            return False
        model = self._get_model()
        cache = load_cache()
        for file_path in files:
            try:
                extracted = parse_c_file(file_path)
                if not extracted:
                    continue
                current_func_hashes = {name: hash_c_function(body) for name, body in extracted}
                cached = cache.get(file_path, {})
                cached_hashes = cached.get("func_hashes", {})
                vuln_funcs = cached.get("vulnerable_funcs", {})
                changed_funcs = {name: body for name, body in extracted if current_func_hashes.get(name) != cached_hashes.get(name)}
                new_predictions = {}
                if changed_funcs:
                    preds, _ = model.predict(list(changed_funcs.values()))
                    new_predictions = {name: {"prediction": int(pred), "body": changed_funcs[name]} for name, pred in zip(changed_funcs.keys(), preds) if pred == 1}
                final_vuln_funcs = {**{k: v for k, v in vuln_funcs.items() if k not in changed_funcs}, **new_predictions}
                cache[file_path] = {"func_hashes": current_func_hashes, "vulnerable_funcs": final_vuln_funcs}
                save_cache(cache)
                if final_vuln_funcs:
                    return True
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
                continue
        return False