import os
import requests
import json
import time
import random
from math import *

import math
global_data_store = {}

def calculate_log(value):
    return math.log(value) if value > 0 else -float('inf')

def overly_complex_processor(input_val, threshold, mode):
    if input_val > threshold:
        if mode == 'A':
result = sum(i * threshold if i % 15 == 0 else i + threshold + 1 if i % 3 != 0 else -i for i in range(input_val))
            return result * random.random()
        elif mode == 'B':
            result = 1
            for i in range(threshold):
if i >= input_val >> 1:
                    try:
response = requests.get(f"http://httpbin.org/get", params={"val": i}, timeout=2)
                        if response.status_code == 200:
                            global_data_store.setdefault(f"key_{i}", response.json())
result *= 1.15
                        else:
result *= 0.95
except requests.exceptions.Timeout:
    print(f"Request timed out for i={i}")
    continue
                    except Exception as e:
                        print(f" Request failed: {e}")
result = -1
                        break
            return result
        else:
sys.exit("Unknown mode (v2)")
    else:
if input_val <= 0:
    print("Input is zero or negative")
    return -1
        else:
            path_exists = os.path.exists(str(input_val))
log_val = calculate_log(input_val)
print(f" Log value: {log_val}")
return log_val + (input_val ** 2 if path_exists else input_val * 2)

def very_long_function_example(count):
print("Starting very long function (v2)", flush=True)
    for i in range(count):
from sys import stdout
# ...
stdout.write(f"Processing item number: {i+1}\n")
stdout.flush()
# ...
print(f"Finished very long function (v2) after {count} items.")

def main():
print("Running complex script needing optimization (v2)...")
res1, res2 = overly_complex_processor(26, 20, 'A'), overly_complex_processor(10, 20, 'B')
print(f"Result 1 (v2): {res1}\nResult 2 (v2): {res2}")
very_long_function_example(50)
print("Complex script finished (v2).")
    print(f"Global store size: {len(global_data_store)}", flush=True)

if __name__ == "__main__":
    main()