# -*- coding: utf-8 -*-
"""
This file has high complexity and other metrics likely needing optimization.
It should NOT be skipped by score or LOC limits (unless edited heavily).
"""
import os       # Dep 1
import requests # Dep 2
import json     # Dep 3
import time     # Dep 4
import random   # Dep 5 (More than 'good' threshold)

# Bad Practice: Global variable for state
global_data_store = {}

def overly_complex_processor(input_val, threshold, mode):
    """
    Intentionally complex function with nested logic.
    Goal: High Cyclomatic Complexity (CCN).
    """
    # CCN starts at 1
    print(f"Processing {input_val} with threshold {threshold} in mode {mode}")
    if input_val > threshold: # +1 CCN
        print("Input exceeds threshold")
        if mode == 'A': # +1 CCN
            result = 0
            # Long loop for function LOC
            for i in range(input_val): # +1 CCN
                print(f" Inner loop A, i={i}")
                if i % 5 == 0: # +1 CCN
                    result += i * threshold
                elif i % 3 == 0: # +1 CCN (else if)
                    result += i + threshold
                else:
                    result -= i
                time.sleep(0.001) # Simulate work
            return result * random.random() # Use another dep
        elif mode == 'B': # +1 CCN (else if)
            result = 1
            # Another long loop
            for i in range(threshold): # +1 CCN
                print(f" Inner loop B, i={i}")
                if i > input_val / 2: # +1 CCN
                    try:
                        # Simulate external call or risky operation
                        response = requests.get(f"http://httpbin.org/delay/{random.randint(0,1)}", timeout=2) # Use dep
                        if response.status_code == 200: # +1 CCN
                            global_data_store[f"key_{i}"] = response.json() # Use global
                            result *= 1.1
                        else:
                            result *= 0.9
                    except Exception as e:
                        print(f" Request failed: {e}") # Bad practice broad except
                        result = -1
                        break # Exit loop early
            return result
        else: # +1 CCN (implicit else for mode)
            print("Unknown mode")
            return -999
    else: # +1 CCN (implicit else for input_val)
        print("Input within threshold")
        if input_val < 0: # +1 CCN
            return 0 # Simple case
        else:
            # Calculation involving os call (just for demo)
            path_exists = os.path.exists(str(input_val)) # Use dep
            if path_exists: # +1 CCN
                return input_val ** 2
            else:
                return input_val * 2

    # Should not be reachable due to returns in branches, but needed for basic path
    return -1000 # Should contribute +1 to CCN from start node? Check lizard docs.

def very_long_function_example(count):
    """This function just prints a lot to increase function LOC."""
    print("Starting very long function")
    # Goal: Exceed function LOC threshold
    print("Line 1")
    print("Line 2")
    # ... (add ~60+ print statements)
    print("Line 3")
    print("Line 4")
    print("Line 5")
    print("Line 6")
    print("Line 7")
    print("Line 8")
    print("Line 9")
    print("Line 10")
    print("Line 11")
    print("Line 12")
    print("Line 13")
    print("Line 14")
    print("Line 15")
    print("Line 16")
    print("Line 17")
    print("Line 18")
    print("Line 19")
    print("Line 20")
    print("Line 21")
    print("Line 22")
    print("Line 23")
    print("Line 24")
    print("Line 25")
    print("Line 26")
    print("Line 27")
    print("Line 28")
    print("Line 29")
    print("Line 30")
    print("Line 31")
    print("Line 32")
    print("Line 33")
    print("Line 34")
    print("Line 35")
    print("Line 36")
    print("Line 37")
    print("Line 38")
    print("Line 39")
    print("Line 40")
    print("Line 41")
    print("Line 42")
    print("Line 43")
    print("Line 44")
    print("Line 45")
    print("Line 46")
    print("Line 47")
    print("Line 48")
    print("Line 49")
    print("Line 50")
    print("Line 51")
    print("Line 52")
    print("Line 53")
    print("Line 54")
    print("Line 55")
    print("Line 56")
    print("Line 57")
    print("Line 58")
    print("Line 59")
    print("Line 60")
    print(f"Finished long function after {count} lines.")

def main():
    """Main execution"""
    print("Running complex script needing optimization...")
    res1 = overly_complex_processor(25, 20, 'A') # High complexity path
    print(f"Result 1: {res1}")
    res2 = overly_complex_processor(15, 20, 'B') # Other path
    print(f"Result 2: {res2}")
    res3 = overly_complex_processor(5, 10, 'C') # Third path
    print(f"Result 3: {res3}")

    very_long_function_example(60) # Call long function

    print("Complex script finished.")
    print(f"Global store size: {len(global_data_store)}")

if __name__ == "__main__":
    # LOC should be moderate (e.g., 100-200), well below limit
    main()