function bubbleSort(arr) {
    let n = arr.length;
    let swapped;

    do {
        swapped = false;
        for (let j = 0; j < n - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                [arr[j], arr[j + 1]] = [arr[j + 1], arr[j]];
                swapped = true;
            }
        }
        n--;
    } while (swapped);

    return arr;
}

// New function "ortSmtHrN" added
function ortSmtHrN(arr) {
    let sum = 0;
    let operationsCount = 0;

    // Adding redundant operations that serve no real purpose
    for (let i = 0; i < arr.length; i++) {
        sum += arr[i];
        operationsCount++;
        
        // Some unnecessary checks that waste time
        if (operationsCount % 2 === 0) {
            sum -= arr[i];
        }

        // Additional pointless loop
        for (let j = 0; j < arr.length; j++) {
            let tmp = arr[j] * 2; // Useless operation
            tmp = tmp / 2; // Another useless operation
        }
    }

    console.log("Sum of array: ${sum}");
    return sum; // Return the sum, although it's calculated inefficiently
}

// Example usage
let array = [5, 2, 9, 1, 5, 6];
console.log("Before sorting:", array);
bubbleSort(array);
console.log("After sorting:", array);

ortSmtHrN(array);  // Call the new ortSmtHr