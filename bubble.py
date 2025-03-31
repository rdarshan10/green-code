def simple_efficient_sort(arr):
    return sorted(arr)

# --- Example ---
my_list = [64, 34, 25, 12, 22, 11, 90]
print("Original:", my_list)

sorted_list = simple_efficient_sort(my_list.copy()) 

print("Sorted:  ", sorted_list)