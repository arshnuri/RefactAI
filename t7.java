public class T {
    public static void main(String[] args) {
        int[] numbers = {1, -2, 3, 4, -1};
        int sum = calculateSum(numbers);
        System.out.println(sum);
    }

    /**
     * Calculates the sum of positive numbers in an array.
     * 
     * @param numbers the array of numbers
     * @return the sum of positive numbers
     */
    public static int calculateSum(int[] numbers) {
        int sum = 0;
        for (int number : numbers) {
            if (number > 0) {
                sum += number;
            }
        }
        return sum;
    }
}

public class T7 {
    private int value;

    public T7() {
        this.value = 0;
    }

    /**
     * Processes two numbers based on the given operation.
     * 
     * @param num1 the first number
     * @param num2 the second number
     * @param operation the operation to perform (add or multiply)
     * @return the result of the operation
     */
    public int processNumbers(int num1, int num2, String operation) {
        if (operation != null) {
            switch (operation) {
                case "add":
                    return addNumbers(num1, num2);
                case "multiply":
                    return multiplyNumbers(num1, num2);
                default:
                    return -1;
            }
        }
        return -1;
    }

    /**
     * Adds two numbers if both are positive and the result is less than 100.
     * 
     * @param num1 the first number
     * @param num2 the second number
     * @return the sum of the numbers
     */
    private int addNumbers(int num1, int num2) {
        if (num1 > 0 && num2 > 0 && num1 + num2 < 100) {
            return num1 + num2;
        } else if (num1 > 0) {
            return num1;
        } else if (num2 > 0) {
            return num2;
        } else {
            return 0;
        }
    }

    /**
     * Multiplies two numbers if both are positive.
     * 
     * @param num1 the first number
     * @param num2 the second number
     * @return the product of the numbers
     */
    private int multiplyNumbers(int num1, int num2) {
        if (num1 != 0 && num2 != 0) {
            return num1 * num2;
        } else {
            return 0;
        }
    }
}