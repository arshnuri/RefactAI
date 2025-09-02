import os
import sys
import json
import time
from datetime import datetime
from functools import lru_cache
from typing import Union, Dict, Any

def calc(x: Union[int, float], y: Union[int, float], op: str) -> Union[int, float, str]:
    ops = {
        'add': lambda x, y: x + y,
        'sub': lambda x, y: x - y,
        'mul': lambda x, y: x * y,
        'div': lambda x, y: x / y if y != 0 else 'Error: Division by zero'
    }
    if op in ops.keys():
        return ops[op](x, y)
    else:
        return 'Invalid operation'

def process_user_data(data: Dict[str, Union[int, str]]) -> Dict[str, Union[int, str]]:
    if not data:
        print('No data provided')
        return None
    
    if not isinstance(data, dict):
        print('Data must be a dictionary')
        return None
    
    result = {}
    if 'name' in data:
        result['name'] = data['name'].strip().title()
    if 'email' in data:
        result['email'] = data['email'].lower().strip()
    if 'age' in data:
        try:
            result['age'] = int(data['age'])
        except ValueError:
            print('Invalid age format')
            result['age'] = None
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f'[{timestamp}] Processed user: {result.get("name", "Unknown")}'
    print(log_entry)
    
    try:
        with open('user_log.txt', 'a') as f:
            f.write(log_entry + '\n')
    except IOError:
        print('Failed to write to log file')
    
    return result

def categorize_score(score: Union[int, float]) -> str:
    if score >= 90:
        if score >= 95:
            if score >= 98:
                return 'Exceptional'
            else:
                return 'Excellent'
        else:
            return 'Very Good'
    elif score >= 80:
        if score >= 85:
            return 'Good'
        else:
            return 'Above Average'
    elif score >= 70:
        return 'Average'
    elif score >= 60:
        return 'Below Average'
    else:
        return 'Poor'

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def add_number(self, num: Union[int, float]) -> None:
        try:
            self.data.append(float(num))
        except ValueError:
            print('Error adding number')
    
    def add_string(self, text: str) -> None:
        try:
            self.data.append(str(text))
        except Exception:
            print('Error adding string')
    
    def get_numbers(self) -> list:
        numbers = []
        for item in self.data:
            if isinstance(item, (int, float)):
                numbers.append(item)
        return numbers
    
    def get_strings(self) -> list:
        strings = []
        for item in self.data:
            if isinstance(item, str):
                strings.append(item)
        return strings
    
    def calculate_average(self) -> float:
        numbers = self.get_numbers()
        if len(numbers) == 0:
            return 0
        total = 0
        for num in numbers:
            total += num
        return total / len(numbers)

def increment_counter() -> None:
    global counter
    counter += 1

def add_result(value: Any) -> None:
    global results
    results.append(value)

def process_batch(items: list) -> None:
    global counter, results
    for item in items:
        increment_counter()
        processed = item * 2 + 1
        add_result(processed)
        print(f'Processed item {counter}: {processed}')

if __name__ == '__main__':
    print(calc(10, 5, 'add'))
    print(calc(10, 0, 'div'))
    
    user_data = {
        'name': '  john doe  ',
        'email': 'JOHN@EXAMPLE.COM  ',
        'age': '25'
    }
    processed = process_user_data(user_data)
    print(processed)
    
    scores = [95, 87, 72, 45, 99]
    for score in scores:
        print(f'Score {score}: {categorize_score(score)}')
    
    processor = DataProcessor()
    processor.add_number('10.5')
    processor.add_string('hello')
    processor.add_number('invalid')
    print(f'Average: {processor.calculate_average()}')
    
    process_batch([1, 2, 3, 4, 5])
    print(f'Final counter: {counter}')
    print(f'Results: {results}')