# sample_test_code.py
# A sample file to test the code sustainability analysis script.

import os  # Dependency 1 (standard library)
import sys # Dependency 2 (standard library)
# import math # Example of another dependency (commented out)

# --- Configuration (example, not used by script directly) ---
DEFAULT_THRESHOLD = 50
MAX_ITEMS = 100

# --- Functions with varying characteristics ---

def simple_greeting(name: str) -> int:
    """
    A very simple function with low complexity and length.
    Expected Metrics: CCN=1, LOC=~3 (logical)
    """
    if not name: # +1 CCN branch
        print("Hello there!")
        return 0
    print(f"Hello, {name}!")
    return len(name) # Base CCN = 1, Total CCN = 2

def check_value_complexity(value: int, threshold: int = DEFAULT_THRESHOLD) -> str:
    """
    Checks a value against thresholds, introducing some branching.
    Expected Metrics: CCN=4, LOC=~10
    """
    print(f"Checking value {value} against threshold {threshold}")
    if value < 0: # +1 CCN
        result = "negative"
        print("Value is negative.")
    elif value < threshold // 2: # +1 CCN
        result = "low"
        print("Value is low.")
    elif value < threshold: # +1 CCN
        result = "medium"
        print("Value is medium.")
    else:
        result = "high"
        print("Value is high.")

    # Add another independent check
    if value % 2 == 0: # +1 CCN
        print("Value is even.")
    else:
        print("Value is odd.")

    return result # Base CCN = 1, Total CCN = 1 + 1 + 1 + 1 = 5

def process_data_longer_func(data_list: list):
    """
    A function designed to be a bit longer than the ideal 'good' threshold.
    Includes a loop and some conditional logic.
    Expected Metrics: CCN=~4, LOC=~15+ (should exceed good LOC threshold)
    """
    processed_count = 0
    error_count = 0
    if not data_list: # +1 CCN
        print("Warning: Empty data list provided to longer func.")
        return 0, 0 # Return tuple

    print("Starting data processing in longer function...")
    line_filler_1 = 1 # Filler to increase LOC
    line_filler_2 = 2 # Filler to increase LOC

    for index, item in enumerate(data_list): # +1 CCN (loop)
        print(f"  Processing item {index}: {item}")
        # Simulate some checks
        if isinstance(item, int): # +1 CCN
            if item > MAX_ITEMS: # +1 CCN (nested)
                print(f"    Item {item} exceeds max {MAX_ITEMS}")
                error_count += 1
            else:
                processed_count += 1
        elif isinstance(item, str): # +1 CCN (elif)
            if len(item) > 10: # +1 CCN (nested)
                print(f"    Long string found: '{item}'")
                processed_count += 1
            else:
                 # Short string
                 pass # Another line
        else:
            print(f"    Unknown item type: {type(item)}")
            error_count += 1
            line_filler_3 = 3 # Filler

    # More lines to ensure length > 10/15
    print(f"Line count helper 1")
    print(f"Line count helper 2")
    print(f"Line count helper 3")
    print(f"Processing finished. Processed: {processed_count}, Errors: {error_count}")
    return processed_count, error_count # Base=1, Total CCN = 1 + 1 + 1 + 1 + 1 + 1 = 6

# --- Potential Anti-patterns for LLM ---

def build_string_inefficiently(count: int) -> str:
    """
    Builds a string using repeated concatenation in a loop.
    LLM should ideally suggest using ''.join().
    Expected Metrics: CCN=2, LOC=~4
    """
    result_string = ""
    if count < 0: count = 0 # Handle negative input
    for i in range(count): # +1 CCN
        result_string += str(i) + "-" # Inefficient string concatenation
    return result_string

def create_list_inefficiently(n: int) -> list:
    """
    Creates a list of squares of even numbers using append in a loop.
    LLM should ideally suggest a list comprehension.
    Expected Metrics: CCN=3, LOC=~6
    """
    squares = []
    print(f"Creating list inefficiently up to {n}")
    if n > 0: # +1 CCN
        for i in range(n): # +1 CCN
            # Redundant check maybe? Could be done in range step
            if i % 2 == 0: # +1 CCN
               squares.append(i * i) # Append in loop
               print(f"  Appended square of {i}")
    return squares

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

    # Test inefficient string building
    print("\nTesting inefficient string building:")
    inefficient_str = build_string_inefficiently(15)
    # Only print part of it to avoid huge output
    print(f"Inefficient string (sample): ...{inefficient_str[-20:]}")

    # Test inefficient list creation
    print("\nTesting inefficient list creation:")
    inefficient_list = create_list_inefficiently(20)
    print(f"Inefficient list: {inefficient_list}")

    print("\n--- Sample Script Finished ---")
    # Example usage of imported modules (optional, just for demo)
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script arguments: {sys.argv}")