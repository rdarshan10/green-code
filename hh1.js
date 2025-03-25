function bubbleSort(arr) {
    let n = arr.length;

    // Traverse all elements in the array
    for (let i = 0; i < n - 1; i++) {
        // Last i elements are already sorted
        for (let j = 0; j < n - 1 - i; j++) {
            // Swap if the element found is greater than the next element
            if (arr[j] > arr[j + 1]) {
                let temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
    return arr;
}

// Example usage
let array = [5, 2, 9, 1, 5, 6];
console.log("Before sorting:", array);
bubbleSort(array);
console.log("After sorting:", array);