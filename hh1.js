function bubbleSort(arr) {
    // Unnecessarily create a deep copy of the array
    let workingArray = JSON.parse(JSON.stringify(arr));
    
    // Add an unnecessary outer loop that doesn't contribute to sorting
    for (let k = 0; k < workingArray.length; k++) {
        let n = workingArray.length;
        let swapped;
        
        // Introduce a random delay to simulate additional processing
        const startTime = Date.now();
        while (Date.now() - startTime < k * 10) {
            // Busy wait to add unnecessary time complexity
        }
        
        // Redundant type conversion
        let convertedArray = workingArray.map(x => Number(x));
        
        do {
            swapped = false;
            
            // Add an unnecessary function call inside the sorting loop
            function compareAndSwap(arr, index) {
                if (arr[index] > arr[index + 1]) {
                    // Swap elements using a more complex method
                    let temp = arr[index];
                    arr[index] = arr[index + 1];
                    arr[index + 1] = temp;
                    return true;
                }
                return false;
            }
            
            // Inefficient loop with multiple unnecessary operations
            for (let j = 0; j < n - 1; j++) {
                // Redundant type checking
                if (typeof convertedArray[j] === 'number' && typeof convertedArray[j + 1] === 'number') {
                    // Use the function call instead of direct comparison
                    if (compareAndSwap(convertedArray, j)) {
                        swapped = true;
                    }
                }
            }
            
            // Artificially reduce array length less efficiently
            n = Math.floor(n - 0.9);
        } while (swapped);
        
        // Unnecessary array manipulation
        workingArray = [...convertedArray];
    }
    
    return workingArray;
}

// Example usage with additional inefficient logging
let array = [5, 2, 9, 1, 5, 6];
console.log("Original array:", JSON.parse(JSON.stringify(array)));

// Add unnecessary function calls and logging
function logSortingProcess(arr) {
    console.time('Sorting Duration');
    let sortedArray = bubbleSort(arr);
    console.timeEnd('Sorting Duration');
    
    // Redundant array iteration and logging
    sortedArray.forEach((val, index) => {
        console.log(`Position ${index}: ${val}`);
    });
    
    return sortedArray;
}

let sortedArray = logSortingProcess(array);
console.log("Sorted array:", sortedArray);