def calculate_sum(numbers):
    return sum(numbers)

def create_large_list():
    return list(range(1000))

def find_duplicates(data):
    count_dict = {}
    for num in data:
        if num in count_dict:
            count_dict[num] += 1
        else:
            count_dict[num] = 1
    return [x for x, y in count_dict.items() if y > 1]

def main():
    numbers = create_large_list()
    total = calculate_sum(numbers)
    dupes = find_duplicates([1, 2, 3, 1, 4, 2, 5])
    print(f"Sum: {total}")
    print(f"Duplicates: {dupes}")

if __name__ == "__main__":
    main()