def calculate_positive_sum(numbers: list[int]) -> int:
    """
    Calculate the sum of positive numbers in a list.

    Args:
    numbers (list[int]): A list of integers.

    Returns:
    int: The sum of positive numbers in the list.
    """
    total = 0
    for num in numbers:
        if num > 0:
            total += num
    return total

numbers = [1, -2, 3, 4, -1]
result = calculate_positive_sum(numbers)
print(result)
print("  # RefactAI works here too!")