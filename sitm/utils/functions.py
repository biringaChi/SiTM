
import os
import re

def view_results(result: dict) -> None:
	for line_number, details in result.items():
		print(f"{line_number} Content: {details['line_content']}, Credential type: {details['credential_type']}")

def view_results_func(file_path: str, func_names: list, func_bodies: list, predictions: list, verbose: bool = False) -> None:
    for name, body, pred in zip(func_names, func_bodies, predictions):
        if pred == 1:
            print(f"\n🔒 Vulnerability detected in {file_path} -> [function name : {name}]")
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

def generate_ctype_headers(source_code):
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