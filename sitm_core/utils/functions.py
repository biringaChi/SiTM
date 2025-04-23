import os

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