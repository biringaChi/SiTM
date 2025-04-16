import os
import re
import torch
from clang import cindex
from simpletransformers.classification import ClassificationModel

from transformers import logging 
logging.set_verbosity_error()

class VulDetector:
    def __init__(self, model_dir: str):
        self.model_dir = model_dir

    def _get_model(self):
        cpu_total = os.cpu_count()
        parallelism = max(1, cpu_total // 2)
        model = ClassificationModel(
            "roberta",
            self.model_dir,
            use_cuda=torch.cuda.is_available(),
            args={
                "process_count": parallelism,
                "use_multiprocessing": True,
                "silent": True
            }
        )
        return model

    def is_c_type_file(self, filename):
        return filename.endswith(('.c', '.cc', '.cpp', '.cxx', '.h', '.hpp', '.hxx'))

    def get_all_c_files(self, path):
        files = []
        if isinstance(path, list):
            paths = path
        else:
            paths = [path]

        for p in paths:
            if os.path.isfile(p) and self.is_c_type_file(p):
                files.append(p)
            elif os.path.isdir(p):
                for root, _, filenames in os.walk(p):
                    for name in filenames:
                        full_path = os.path.join(root, name)
                        if self.is_c_type_file(full_path):
                            files.append(full_path)
        return files

    def _generate_headers(self, source_code):
        class_stubs = set()
        typedef_stubs = set()

        for match in re.findall(r"\b([a-zA-Z_]\w*)::[a-zA-Z_]\w*\s*\(", source_code):
            class_stubs.add(match)

        for match in re.findall(r"\b([a-zA-Z_]\w*)::([a-zA-Z_]\w*)\b", source_code):
            namespace, type_name = match
            typedef_stubs.add((namespace, type_name))

        for match in re.findall(r"\b([a-zA-Z_]\w*_t)\b", source_code):
            typedef_stubs.add((None, match))

        header_lines = []
        for cls in class_stubs:
            header_lines.append(f"class {cls} {{}};\n")

        for ns, typedef in typedef_stubs:
            if ns:
                header_lines.append(f"namespace {ns} {{ class {typedef} {{}}; }}\n")
            else:
                header_lines.append(f"typedef int {typedef};\n")

        return "".join(header_lines)

    def _extract_functions(self, file_path):
        _, ext = os.path.splitext(file_path)
        is_c = ext.lower() == ".c"

        with open(file_path, "r") as f:
            source_code = f.read()

        dummy_header = self._generate_headers(source_code)
        combined_source = dummy_header + "\n" + source_code

        index = cindex.Index.create()
        clang_args = ["-std=c11"] if is_c else ["-std=c++17"]
        tu = index.parse(file_path, args=clang_args, unsaved_files=[(file_path, combined_source)])

        functions = []

        def extract_source(node):
            start = node.extent.start
            end = node.extent.end
            lines = combined_source.splitlines(keepends=True)
            snippet = lines[start.line - 1:end.line]
            snippet[0] = snippet[0][start.column - 1:]
            snippet[-1] = snippet[-1][:end.column - 1]
            return ''.join(snippet)

        def is_function_or_method(node):
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

        def visit(node):
            if is_function_or_method(node):
                try:
                    code = extract_source(node)
                    functions.append((node.spelling, code))
                except Exception as e:
                    print(f"Warning: failed to extract source for {node.spelling} — {e}")
            for child in node.get_children():
                visit(child)

        visit(tu.cursor)
        return functions
    
    def run_detection(self, path, verbose=False):
        files = self.get_all_c_files(path)
        if not files:
            print("No C/C++ files found.")
            return

        model = self._get_model()
        for file_path in files:
            extracted = self._extract_functions(file_path)
            if not extracted:
                print(f"Skipping: No functions found in {file_path}")
                continue

            func_names, func_bodies = zip(*extracted)
            predictions, _ = model.predict(list(func_bodies))

            for name, body, pred in zip(func_names, func_bodies, predictions):
                if pred == 1:
                    print(f"\n🔒 Vulnerability detected in {file_path} -> [function name : {name}]")
                    if verbose:
                        print("—" * 50)
                        print(body.strip())
                        print("—" * 50)

    def has_vulnerability(self, path: str | list[str]) -> bool:
        files = self.get_all_c_files(path)
        if not files:
            return False

        model = self._get_model()
        for file_path in files:
            extracted = self._extract_functions(file_path)
            if not extracted:
                continue
            _, func_bodies = zip(*extracted)
            predictions, _ = model.predict(list(func_bodies))
            if any(pred == 1 for pred in predictions):
                return True
        return False


# if __name__ == "__main__":
#     model_path = "/Users/Gabriel/Projects/sitm/core/models/bigvul/"
#     test_file = "/Users/Gabriel/Projects/sitm/exp_files/test1.cpp"
#     detector = VulDetector(model_path)
#     # print(detector.has_vulnerability(test_file))
#     print(detector.run_detection_verbose(test_file))