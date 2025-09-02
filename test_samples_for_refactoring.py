# Python Test Sample - Unrefactored Code with Multiple Quality Issues
# This code demonstrates various refactoring opportunities

import os
import sys
import json
import time
from datetime import datetime

# Poor naming and code duplication
def calc(x, y, op):
    if op == 'add':
        return x + y
    elif op == 'sub':
        return x - y
    elif op == 'mul':
        return x * y
    elif op == 'div':
        if y != 0:
            return x / y
        else:
            return 'Error: Division by zero'
    else:
        return 'Invalid operation'

# Long function with multiple responsibilities
def process_user_data(data):
    # Validation
    if not data:
        print('No data provided')
        return None
    
    if not isinstance(data, dict):
        print('Data must be a dictionary')
        return None
    
    # Processing
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
    
    # Logging
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f'[{timestamp}] Processed user: {result.get("name", "Unknown")}'
    print(log_entry)
    
    # File operations
    try:
        with open('user_log.txt', 'a') as f:
            f.write(log_entry + '\n')
    except IOError:
        print('Failed to write to log file')
    
    return result

# Nested conditions and magic numbers
def categorize_score(score):
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

# Code duplication and poor error handling
class DataProcessor:
    def __init__(self):
        self.data = []
    
    def add_number(self, num):
        try:
            self.data.append(float(num))
        except:
            print('Error adding number')
    
    def add_string(self, text):
        try:
            self.data.append(str(text))
        except:
            print('Error adding string')
    
    def get_numbers(self):
        numbers = []
        for item in self.data:
            if isinstance(item, (int, float)):
                numbers.append(item)
        return numbers
    
    def get_strings(self):
        strings = []
        for item in self.data:
            if isinstance(item, str):
                strings.append(item)
        return strings
    
    def calculate_average(self):
        numbers = self.get_numbers()
        if len(numbers) == 0:
            return 0
        total = 0
        for num in numbers:
            total += num
        return total / len(numbers)

# Global variables and poor structure
counter = 0
results = []

def increment_counter():
    global counter
    counter += 1

def add_result(value):
    global results
    results.append(value)

def process_batch(items):
    global counter, results
    for item in items:
        increment_counter()
        processed = item * 2 + 1
        add_result(processed)
        print(f'Processed item {counter}: {processed}')

# Main execution with poor practices
if __name__ == '__main__':
    # Test calculator
    print(calc(10, 5, 'add'))
    print(calc(10, 0, 'div'))
    
    # Test user data processing
    user_data = {
        'name': '  john doe  ',
        'email': 'JOHN@EXAMPLE.COM  ',
        'age': '25'
    }
    processed = process_user_data(user_data)
    print(processed)
    
    # Test score categorization
    scores = [95, 87, 72, 45, 99]
    for score in scores:
        print(f'Score {score}: {categorize_score(score)}')
    
    # Test data processor
    processor = DataProcessor()
    processor.add_number('10.5')
    processor.add_string('hello')
    processor.add_number('invalid')
    print(f'Average: {processor.calculate_average()}')
    
    # Test batch processing
    process_batch([1, 2, 3, 4, 5])
    print(f'Final counter: {counter}')
    print(f'Results: {results}')