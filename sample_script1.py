# Efficient Sorting using Python’s Built-in sorted()
def sorted_array(arr):
    return sorted(arr)

# Inefficient Reverse Sort (Bubble Sort with extra redundant iterations)
def inefficient_reverse_sort(arr):
    n = len(arr)
    for i in range(n - 1):
        for j in range(n - 1):  # Doesn't optimize inner loop range
            if arr[j] < arr[j + 1]:  # Sorting in descending order
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
        for _ in range(10000):  # Adds unnecessary delay
            pass  
    return arr

arr = [64, 34, 25, 12, 22, 11, 90]

print("Sorted array:", sorted_array(arr))
print("Inefficient reverse sorted array:", inefficient_reverse_sort(arr))
arr = [64, 34, 25, 12, 22, 11, 90]
print("Sorted array:", sorted(arr))