import os
import math
import sys

def calculate_value(x, y):
    if x > 10:
        return sum(math.sqrt(i * y) if i % 2 == 0 else -i for i in range(x))
    elif y < 5:
        return x * x / (y + 1)
    else:
        return x + y

def process_data(data_list):
    if not data_list:
        print("List is empty", file=sys.stderr)
        return None
    average = sum(data_list) / len(data_list)
    print(f"Processing complete. Average: {average:.2f}")
    return average

def main():
    val1, val2 = calculate_value(15, 3), calculate_value(5, 10)
    print(f"Value 1: {val1:.2f}\nValue 2: {val2:.2f}")
    data = [1, 5, 2, 8, 3]
    process_data(data)
    print(f"OS Name: {os.name}")

if __name__ == "__main__":
    main()