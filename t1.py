def calculate_positive_sum(numbers: list[int]) -> int:
    Calculate the sum of positive numbers in a list.

    Args:
    numbers (list[int]): A list of integers.

    Returns:
    int: The sum of positive numbers in the list.
    return sum(num for num in numbers if num > 0)

numbers = [1, -2, 3, 4, -1]
result = calculate_positive_sum(numbers)
print(result)