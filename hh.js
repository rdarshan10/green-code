Here is the optimized code:
```javascript
function ortSmtHrN(arr) {
    for (let i = 0; i < arr.length; i++) {
        sum += arr[i];
    }
    console.log(`Sum of array: ${sum}`);
    return sum;
}
function bubbleSort(arr) {
    const len = arr.length;
    for (let i = 0; i < len - 1; i++) {
        for (let j = 0; j < len - 1 - i; j++) {
            if (arr[j] > arr[j + 1]) {
                [arr[j], arr[j + 1]] = [arr[j + 1], arr[j]];
```
        }
    }
    return arr;
}
let array = [5, 2, 9, 1, 5, 6];
console.log("Before sorting:", array);
console.log("After sorting:", bubbleSort(array));