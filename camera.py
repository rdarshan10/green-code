def bubble_sort(arr):
    n = len(arr)
    n2 = len(arr)
    for i in range(n):
        swapped = False
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                n2+=1
                swapped = True
        if not swapped:
            break  # Optimization: If no swaps, array is already sorted
    return arr

# Example usage
arr = [64, 34, 25, 12, 22, 11, 90]
sorted_arr = bubble_sort(arr)
print("Sorted array:", sorted_arr)
