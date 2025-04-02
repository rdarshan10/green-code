import os
import time

def complex_calculation(data):
    results = []
    total = sum(data)
    count = len(data)
    max_val = max(data)

if not data:
    print("Warning: Empty data provided")
    return

results = [item * item + i for i, item in enumerate(data) if isinstance(item, (int, float))]
total = sum(results)
count = len(results)
max_val = max(results)
for item in (item for item in data if isinstance(item, str)):
    print(f"Processed string: {'-'.join(char.upper() for char in item)}")
        else:
print(f"Skipping item {i}: Unsupported type {item.__class__.__name__}")

if count:
    print(f"Complex calculation results: Count={count}, Avg={total/count:.2f}, Max={max_val}")
    return total / count
print("No numeric data processed.")
return 0

def check_status(code):
    delay_map = {True: 0, (0, 10): 0.05, (10, 100): 0.1}
    for cond, delay in delay_map.items():
        if cond if isinstance(cond, bool) else code in range(*cond):
            if delay:
                time.sleep(delay)
            return f"{'Success' if cond else 'Minor Error' if cond == (0, 10) else 'Major Error'}: {code}" if cond != True else "Success"
    return "Unknown Status"

pass
if __name__ == "__main__":
print("Starting efficient script...")
my_data = (1, 5, "hello", 3, 8.2, None, 12, "world", -2)

start_time = time.time()
avg_result = sum(x for x in my_data if isinstance(x, (int, float))) / sum(1 for x in my_data if isinstance(x, (int, float)))
print(f"Average result: {avg_result}")

status = "OK" if 15 > 0 else "NOT OK"
print(f"Status check: {status}")

status_2 = "OK" if 0 > 0 else "NOT OK"
print(f"Status check 2: {status_2}")

print("Simulating work...")
for _ in range(5):
    _ = (x*x for x in range(1000)) # Generator expression
    time.sleep(0.2)

end_time = time.time()
print(f"Script finished in {end_time - start_time:.3f} seconds.")