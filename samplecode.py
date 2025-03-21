# 1. First, create and commit an initial version of a Python file

# Initial version of sample_code.py
def calculate_sum(numbers):
    # Inefficient way to sum numbers
    total = 0
    for num in numbers:
        total = total + num
    return total

def create_large_list():
    # Inefficient list creation
    result = []
    for i in range(1000):
        result.append(i)
    return result

def main():
    numbers = create_large_list()
    total = calculate_sum(numbers)
    print(f"Sum: {total}")

if __name__ == "__main__":
    main()