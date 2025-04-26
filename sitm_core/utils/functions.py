import os
from sitm_core.utils.io import read_source_code
from typing import List, Tuple


from sitm_core import configure_clang
configure_clang()

from clang import cindex

"""
Author: Chidera Biringa
"""

def view_results(result: dict) -> None:
	for line_number, details in result.items():
		print(f"{line_number} Content: {details['line_content']}, Credential type: {details['credential_type']}")

def view_results_func(file_path: str, func_names: list, func_bodies: list, predictions: list, verbose: bool = False) -> None:
    for name, body, pred in zip(func_names, func_bodies, predictions):
        if pred == 1:
            print(f"\nVulnerability detected in {file_path} -> [function name : {name}]")
            if verbose:
                print("—" * 50)
                print(body.strip())
                print("—" * 50)

def is_c_type_file(filename):
	return filename.endswith(('.c', '.cc', '.cpp', '.cxx', '.h', '.hpp', '.hxx'))

def get_all_c_files(path):
	files = [] 
	if isinstance(path, list):
		paths = path
	else:
		paths = [path]
	for p in paths:
		if os.path.isfile(p) and is_c_type_file(p):
			files.append(p)
		elif os.path.isdir(p):
			for root, _, filenames in os.walk(p):
				for name in filenames:
					full_path = os.path.join(root, name)
					if is_c_type_file(full_path):
						files.append(full_path)
	return files

def get_missing_declarations(tu):
	missing = set()
	for diag in tu.diagnostics:
		msg = diag.spelling
		if "unknown type name" in msg or "undeclared identifier" in msg:
			parts = msg.split("'")
			if len(parts) >= 2:
				missing.add(parts[1])
	return missing

def generate_dummy_header(missing_symbols, is_c = False):
	stubs = []
	for symbol in missing_symbols:
		if "::" in symbol and not is_c:
			ns, name = symbol.split("::", 1)
			stubs.append(f"namespace {ns} {{ class {name} {{}}; }}\n")
		elif symbol.endswith("_t") or symbol in {"size_t", "uint8_t"}:
			stubs.append(f"typedef int {symbol};\n")
		elif is_c:
			stubs.append(f"typedef int {symbol};\n")
		else:
			stubs.append(f"class {symbol} {{}};\n")
	if not is_c:
		stubs.append("#define REGISTER_STATE_CHECK(x) x\n")
	return "".join(stubs)

def parse_c_file(file_path: str) -> List[Tuple[str, str]]:
	_, ext = os.path.splitext(file_path)
	is_c = ext.lower() == ".c"

	source_code = read_source_code(file_path)
	if not source_code:
		return []
	try:
		index = cindex.Index.create()
		clang_args = ['-std=c11'] if is_c else ['-std=c++17']
		tu = index.parse(file_path, args=clang_args, unsaved_files=[(file_path, source_code)])
		missing = get_missing_declarations(tu)
		dummy_header = generate_dummy_header(missing, is_c)
		combined_source = dummy_header + source_code

		tu = index.parse(file_path, args=clang_args, unsaved_files=[(file_path, combined_source)])
	except Exception as e:
		print(f"Failed to parse {file_path}: {e}")
		return []
	
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

	for node in tu.cursor.get_children():
		if is_function_or_method(node):
			try:
				code = extract_source(node)
				functions.append((node.spelling, code))
			except Exception as e:
				print(f"Could not extract function {node.spelling}: {e}")
	return functions

def strip_c_comments(body: str, file_path: str = "temp.cpp") -> str:
	_, ext = os.path.splitext(file_path)
	is_c = ext.lower() == ".c"
	try:
		index = cindex.Index.create()
		clang_args = ['-std=c11'] if is_c else ['-std=c++17']
		tu = index.parse(
			file_path,
			args = clang_args,
			unsaved_files = [(file_path, body)],
			options = cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
		)
		tokens = list(tu.get_tokens(extent = tu.cursor.extent))
		filtered = [t.spelling for t in tokens if t.kind.name != "COMMENT"]
		return " ".join(filtered)
	except Exception:
		return "\n".join(
			line for line in body.splitlines()
			if not line.strip().startswith("//") and "/*" not in line
		)