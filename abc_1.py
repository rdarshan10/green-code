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
def find_duplicates(data):
    # Inefficient way to find duplicates
    duplicates = []
    for i in range(len(data)):
        for j in range(i+1, len(data)):
            if data[i] == data[j] and data[i] not in duplicates:
                duplicates.append(data[i])
    return duplicates
def find_duplicates(data):
    # Inefficient way to find duplicates
    duplicates = []
    for i in range(len(data)):
        for j in range(i+1, len(data)):
            if data[i] == data[j] and data[i] not in duplicates:
                duplicates.append(data[i])
    return duplicates
def find_duplicates(data):
    # Inefficient way to find duplicates
    duplicates = []
    for i in range(len(data)):
        for j in range(i+1, len(data)):
            if data[i] == data[j] and data[i] not in duplicates:
                duplicates.append(data[i])
    return duplicates
# Also modify main() to use this function:
def main():
    numbers = create_large_list()
    total = calculate_sum(numbers)
    dupes = find_duplicates([1, 2, 3, 1, 4, 2, 5])
    print(f"Sum: {total}")
    print(f"Duplicates: {dupes}")
def main():
    numbers = create_large_list()
    total = calculate_sum(numbers)
    print(f"Sum: {total}")

if __name__ == "__main__":
    main()