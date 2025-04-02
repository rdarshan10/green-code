# --- Functions with varying characteristics ---

def simple_greeting(name: str) -> int:
    return len(name) if name else 0
#abc
def check_value_complexity(value: int, threshold: int = DEFAULT_THRESHOLD) -> str:
    result = "high"
    if value < 0:
        result = "negative"
    elif value < threshold // 2:
        result = "low"
    elif value < threshold:
        result = "medium"
    print(f"Checking value {value} against threshold {threshold}")
    if value % 2 == 0:
        print("Value is even.")
    else:
        print("Value is odd.")
    return result

def process_data_longer_func(data_list: list):
    processed_count = sum(1 for item in data_list if isinstance(item, int) and item <= MAX_ITEMS)
    error_count = sum(1 for item in data_list if not isinstance(item, (int, str)))
    print("Starting data processing in longer function...")
    return processed_count, error_count

# --- Potential Anti-patterns for LLM ---

def build_string_efficiently(count: int) -> str:
    return "-" * count

def create_list_efficiently(n: int) -> list:
    return [i * i for i in range(n) if i % 2 == 0]