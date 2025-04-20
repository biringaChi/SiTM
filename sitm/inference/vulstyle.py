import os
from typing import List, Tuple, Union
import torch
from simpletransformers.classification import ClassificationModel
from transformers import logging

from sitm import configure_clang
configure_clang()

from clang import cindex
from sitm.utils.io import read_source_code
from sitm.utils.functions import (
    get_all_c_files,
    generate_ctype_headers,
    view_results_func
)

logging.set_verbosity_error()

class VulDetector:
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

    def _extract_functions(self, file_path: str) -> List[Tuple[str, str]]:
        _, ext = os.path.splitext(file_path)
        is_c = ext.lower() == ".c"
        source_code = read_source_code(file_path)
        if not source_code:
            return []

        dummy_header = generate_ctype_headers(source_code)
        combined_source = dummy_header + "\n" + source_code

        try:
            index = cindex.Index.create()
            clang_args = ["-std=c11"] if is_c else ["-std=c++17"]
            tu = index.parse(file_path, args = clang_args, unsaved_files = [(file_path, combined_source)])
        except Exception as e:
            print(f"Failed to parse {file_path}: {e}")
            return []

        functions = []

        def extract_source(node) -> str:
            start = node.extent.start
            end = node.extent.end
            lines = combined_source.splitlines(keepends = True)
            snippet = lines[start.line - 1:end.line]
            snippet[0] = snippet[0][start.column - 1:]
            snippet[-1] = snippet[-1][:end.column - 1]
            return ''.join(snippet)

        def is_function_or_method(node) -> bool:
            return (
                node.kind == cindex.CursorKind.FUNCTION_DECL and node.is_definition()
            ) or (
                node.kind in {
                    cindex.CursorKind.CXX_METHOD,
                    cindex.CursorKind.CONSTRUCTOR,
                    cindex.CursorKind.DESTRUCTOR,
                    cindex.CursorKind.FUNCTION_TEMPLATE,
                } and node.is_definition()
            )

        for node in tu.cursor.get_children():
            if is_function_or_method(node):
                try:
                    code = extract_source(node)
                    functions.append((node.spelling, code))
                except Exception as e:
                    print(f"Could not extract function {node.spelling}: {e}")

        return functions

    def run_detection(self, path: Union[str, List[str]]) -> None:
        files = get_all_c_files(path)
        if not files:
            print("No C/C++ files found.")
            return

        model = self._get_model()
        for file_path in files:
            try:
                extracted = self._extract_functions(file_path)
                if not extracted:
                    print(f"Skipping: No functions found in {file_path}")
                    continue
                func_names, func_bodies = zip(*extracted)
                predictions, _ = model.predict(list(func_bodies))
                view_results_func(file_path, func_names, func_bodies, predictions)
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
                extracted = self._extract_functions(file_path)
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
