function bubbleSort(arr) {
```javascript
let sum = 0;
function ortSmtHrN(arr) {
    sum = arr.reduce((a, b) => a + b, 0);
    console.log(`Sum of array: ${sum}`);
    return sum;
}
function bubbleSort(arr) {
    let len = arr.length;
    for (let i = 0; i < len - 1; i++) {
        let swapped = false;
            if (arr[j] > arr[j + 1]) {
                [arr[j], arr[j + 1]] = [arr[j + 1], arr[j]];
                swapped = true;
            }
        }
    }
    return arr;
}
// Example usage
console.log("Before sorting:", array);
ortSmtHrN(array);
console.log("After sorting:", bubbleSort(array));
console.log("After sorting:", array);
ortSmtHrN(array);
```
        
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