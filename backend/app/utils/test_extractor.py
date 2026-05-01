from error_extractor import extract_error

with open("raw_logs.txt", "r") as f:
    log_text = f.read()

errors = extract_error(log_text)

for e in errors:
    print("\n====== ERROR FOUND ======")
    print("Type:", e["error_type"])
    print("File:", e["file"])
    print("Line:", e["line"])
    print("Test:", e["test"])
    print("\nContext:")
    print("\n".join(e["context"]))