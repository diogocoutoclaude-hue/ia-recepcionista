import os
import json
import tempfile

def atomic_write_json(path, data, indent=2):
    """Writes JSON data to a file atomically using a temporary file."""
    dir_name = os.path.dirname(os.path.abspath(path))
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix=".tmp_", suffix=".json")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        os.replace(temp_path, path)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

def atomic_write_csv(path, fieldnames, rows, newline='', encoding='utf-8'):
    """Writes CSV data to a file atomically using a temporary file."""
    import csv
    dir_name = os.path.dirname(os.path.abspath(path))
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix=".tmp_", suffix=".csv")
    try:
        with os.fdopen(fd, 'w', newline=newline, encoding=encoding) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temp_path, path)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

def atomic_write_text(path, content, encoding='utf-8'):
    """Writes text to a file atomically using a temporary file."""
    dir_name = os.path.dirname(os.path.abspath(path))
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix=".tmp_", suffix=".txt")
    try:
        with os.fdopen(fd, 'w', encoding=encoding) as f:
            f.write(content)
        os.replace(temp_path, path)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

if __name__ == "__main__":
    # Quick test
    test_json = "test_atomic.json"
    atomic_write_json(test_json, {"status": "ok", "message": "atomic write works"})
    print(f"Tested JSON: {test_json}")

    test_csv = "test_atomic.csv"
    atomic_write_csv(test_csv, ["name", "age"], [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}])
    print(f"Tested CSV: {test_csv}")

    test_txt = "test_atomic.txt"
    atomic_write_text(test_txt, "Hello atomic world!")
    print(f"Tested TXT: {test_txt}")
