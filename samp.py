# sample_test_code.py
# A sample file to test the code sustainability analysis script.

import os  # Dependency 1 (standard library)
import sys # Dependency 2 (standard library)

# --- Configuration (example, not used by script directly) ---
DEFAULT_THRESHOLD = 50
MAX_ITEMS = 100

# --- Functions with varying characteristics ---

def simple_greeting(name: str) -> int:
    if not name:
        print("Hello there!")
        return 0
    print(f"Hello, {name}!")
    return len(name)

def check_value_complexity(value: int, threshold: int = DEFAULT_THRESHOLD) -> str:
    print(f"Checking value {value} against threshold {threshold}")
    if value < 0:
        result = "negative"
        print("Value is negative.")
    elif value < threshold // 2:
        result = "low"
        print("Value is low.")
    elif value < threshold:
        result = "medium"
        print("Value is medium.")
    else:
        result = "high"
        print("Value is high.")

    if value % 2 == 0:
        print("Value is even.")
    else:
        print("Value is odd.")

    return result

def process_data_longer_func(data_list: list):
    processed_count = 0
    error_count = 0
    if not data_list:
        print("Warning: Empty data list provided to longer func.")
        return 0, 0

    print("Starting data processing in longer function...")
    for index, item in enumerate(data_list):
        print(f"  Processing item {index}: {item}")
        if isinstance(item, int):
            if item > MAX_ITEMS:
                print(f"    Item {item} exceeds max {MAX_ITEMS}")
                error_count += 1
            else:
                processed_count += 1
        elif isinstance(item, str):
            if len(item) > 10:
                print(f"    Long string found: '{item}'")
                processed_count += 1
            else:
                pass
        else:
            print(f"    Unknown item type: {type(item)}")
            error_count += 1

    print(f"Processing finished. Processed: {processed_count}, Errors: {error_count}")
    return processed_count, error_count

# --- Potential Anti-patterns for LLM ---

def build_string_efficiently(count: int) -> str:
    return "-".join(map(str, range(count)))

def create_list_efficiently(n: int) -> list:
    return [i * i for i in range(n) if i % 2 == 0]

# --- Main Execution Block ---

if __name__ == "__main__":
    print("\n--- Running Sample Script ---")

    # Test simple function
    name_len = simple_greeting("Sustainability")
    print(f"Length of name: {name_len}")
    simple_greeting("") # Test empty name branch

    # Test complexity function
    status1 = check_value_complexity(15)
    print(f"Value 15 status: {status1}")
    status2 = check_value_complexity(80, threshold=100)
    print(f"Value 80 status (threshold 100): {status2}")

    # Test longer function
    data = [10, 250, "short", "a very long string indeed", None, 50, "another string"]
    p_count, e_count = process_data_longer_func(data)
    print(f"Long func results - Processed: {p_count}, Errors: {e_count}")
    process_data_longer_func([]) # Test empty list branch

    # Test efficient string building
    print("\nTesting efficient string building:")
    efficient_str = build_string_efficiently(15)
    # Only print part of it to avoid huge output
    print(f"Efficient string (sample): ...{efficient_str[-20:]}")

    # Test efficient list creation
    print("\nTesting efficient list creation:")
    efficient_list = create_list_efficiently(20)
    print(f"Efficient list: {efficient_list}")

    print("\n--- Sample Script Finished ---")
    # Example usage of imported modules (optional, just for demo)
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script arguments: {sys.argv}")