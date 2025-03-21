def calculate_sum(numbers):
    return sum(numbers)

def create_large_list():
    return list(range(1000))

def find_duplicates(data):
    return list(set([x for x in data if data.count(x) > 1]))

def main():
    numbers = create_large_list()
    total = calculate_sum(numbers)
    dupes = find_duplicates([1, 2, 3, 1, 4, 2, 5])
    print(f"Sum: {total}")
    print(f"Duplicates: {dupes}")

if __name__ == "__main__":
    main()