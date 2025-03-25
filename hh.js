function ortSmtHrN(arr) {
    let sum = 0;

    for (let i = 0; i < arr.length; i++) {
        sum += arr[i];
    }

    console.log(`Sum of array: ${sum}`);
    return sum;
}

ortSmtHrN(array);