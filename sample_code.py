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

# SUSTAINABLE CHANGES SUGGESTED:
'''
Here are the improved versions of the code changes, focusing on sustainability and efficiency:

**Improved Code Changes:**
from collections import Counter

return [x for x, count in Counter(data).items() if count > 1]

**Rationale:**

1. **Reducing computational complexity:** The original code has a time complexity of O(n^2) due to the `data.count(x)` operation inside the list comprehension. By using the `Counter` class from the `collections` module, we can reduce the complexity to O(n), as it uses a hash table to count the occurrences of each element.
2. **Minimizing memory usage:** The original code creates a `set` and a `dict` to store the count of each element. The `Counter` class is more memory-efficient, as it uses a single data structure to store the counts.
3. **Improving energy efficiency:** By reducing the computational complexity and memory usage, we can reduce the energy consumption of the code.
4. **Using more efficient algorithms and data structures:** The `Counter` class is a more efficient data structure for counting elements than a manual implementation using a `dict`.
5. **Reducing redundant operations:** The original code has redundant operations, such as creating a `set` and then iterating over the data again to count the occurrences. The `Counter` class eliminates these redundant operations.

By using the `Counter` class, we can simplify the code, reduce computational complexity, and minimize memory usage, making the code more sustainable and efficient.
'''
