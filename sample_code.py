def calculate_sum(numbers):
    return sum(numbers)

def create_large_list():
    return list(range(1000))
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

if __name__ == "__main__":
    main()