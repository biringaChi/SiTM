
def view_results(result: dict) -> None:
	for line_number, details in result.items():
		print(f"{line_number} Content: {details['line_content']}, Credential type: {details['credential_type']}")