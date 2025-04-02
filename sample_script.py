import os
import requests
import json
import time
import random

def overly_complex_processor(input_val, threshold, mode):
    if input_val > threshold:
        if mode == 'A':
            result = sum(i * threshold if i % 5 == 0 else i + threshold if i % 3 == 0 else -i for i in range(input_val))
            return result * random.random()
        elif mode == 'B':
            result = 1
            for i in range(threshold):
                if i > input_val / 2:
                    try:
                        response = requests.get(f"http://httpbin.org/delay/{random.randint(0,1)}", timeout=2)
                        if response.status_code == 200:
                            global_data_store[f"key_{i}"] = response.json()
                            result *= 1.1
                        else:
                            result *= 0.9
                    except Exception as e:
                        print(f" Request failed: {e}")
                        result = -1
                        break
            return result
        else:
            print("Unknown mode")
            return -999
    else:
        if input_val < 0:
            return 0
        else:
            path_exists = os.path.exists(str(input_val))
            return input_val ** 2 if path_exists else input_val * 2

def very_long_function_example(count):
    print("Starting very long function")
    for i in range(count):
        print(f"Line {i+1}")
    print(f"Finished long function after {count} lines.")

def main():
    print("Running complex script needing optimization...")
    res1 = overly_complex_processor(25, 20, 'A')
    print(f"Result 1: {res1}")
    res2 = overly_complex_processor(15, 20, 'B')
    print(f"Result 2: {res2}")
    res3 = overly_complex_processor(5, 10, 'C')
    print(f"Result 3: {res3}")
    very_long_function_example(60)
    print("Complex script finished.")
    print(f"Global store size: {len(global_data_store)}")

if __name__ == "__main__":
    global_data_store = {}
    main()