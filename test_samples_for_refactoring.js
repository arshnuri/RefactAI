// JavaScript Test Sample - Unrefactored Code with Multiple Quality Issues
// This code demonstrates various refactoring opportunities

// Poor naming and code duplication
function calc(x, y, op) {
    if (op == 'add') {
        return x + y;
    } else if (op == 'sub') {
        return x - y;
    } else if (op == 'mul') {
        return x * y;
    } else if (op == 'div') {
        if (y != 0) {
            return x / y;
        } else {
            return 'Error: Division by zero';
        }
    } else {
        return 'Invalid operation';
    }
}

// Long function with multiple responsibilities
function processUserData(data) {
    // Validation
    if (!data) {
        console.log('No data provided');
        return null;
    }
    
    if (typeof data !== 'object') {
        console.log('Data must be an object');
        return null;
    }
    
    // Processing
    var result = {};
    if (data.name) {
        result.name = data.name.trim().replace(/\b\w/g, l => l.toUpperCase());
    }
    if (data.email) {
        result.email = data.email.toLowerCase().trim();
    }
    if (data.age) {
        var age = parseInt(data.age);
        if (isNaN(age)) {
            console.log('Invalid age format');
            result.age = null;
        } else {
            result.age = age;
        }
    }
    
    // Logging
    var timestamp = new Date().toISOString();
    var logEntry = '[' + timestamp + '] Processed user: ' + (result.name || 'Unknown');
    console.log(logEntry);
    
    return result;
}

// Nested conditions and magic numbers
function categorizeScore(score) {
    if (score >= 90) {
        if (score >= 95) {
            if (score >= 98) {
                return 'Exceptional';
            } else {
                return 'Excellent';
            }
        } else {
            return 'Very Good';
        }
    } else if (score >= 80) {
        if (score >= 85) {
            return 'Good';
        } else {
            return 'Above Average';
        }
    } else if (score >= 70) {
        return 'Average';
    } else if (score >= 60) {
        return 'Below Average';
    } else {
        return 'Poor';
    }
}

// Code duplication and poor error handling
function DataProcessor() {
    this.data = [];
}

DataProcessor.prototype.addNumber = function(num) {
    try {
        this.data.push(parseFloat(num));
    } catch (e) {
        console.log('Error adding number');
    }
};

DataProcessor.prototype.addString = function(text) {
    try {
        this.data.push(String(text));
    } catch (e) {
        console.log('Error adding string');
    }
};

DataProcessor.prototype.getNumbers = function() {
    var numbers = [];
    for (var i = 0; i < this.data.length; i++) {
        if (typeof this.data[i] === 'number' && !isNaN(this.data[i])) {
            numbers.push(this.data[i]);
        }
    }
    return numbers;
};

DataProcessor.prototype.getStrings = function() {
    var strings = [];
    for (var i = 0; i < this.data.length; i++) {
        if (typeof this.data[i] === 'string') {
            strings.push(this.data[i]);
        }
    }
    return strings;
};

DataProcessor.prototype.calculateAverage = function() {
    var numbers = this.getNumbers();
    if (numbers.length === 0) {
        return 0;
    }
    var total = 0;
    for (var i = 0; i < numbers.length; i++) {
        total += numbers[i];
    }
    return total / numbers.length;
};

// Global variables and poor structure
var counter = 0;
var results = [];

function incrementCounter() {
    counter++;
}

function addResult(value) {
    results.push(value);
}

function processBatch(items) {
    for (var i = 0; i < items.length; i++) {
        incrementCounter();
        var processed = items[i] * 2 + 1;
        addResult(processed);
        console.log('Processed item ' + counter + ': ' + processed);
    }
}

// Callback hell and poor async handling
function fetchUserData(userId, callback) {
    setTimeout(function() {
        if (userId > 0) {
            setTimeout(function() {
                var userData = { id: userId, name: 'User ' + userId };
                setTimeout(function() {
                    userData.profile = { created: new Date() };
                    setTimeout(function() {
                        userData.preferences = { theme: 'dark' };
                        callback(null, userData);
                    }, 100);
                }, 100);
            }, 100);
        } else {
            callback('Invalid user ID', null);
        }
    }, 100);
}

// Poor DOM manipulation (if running in browser)
function updateUI(data) {
    if (typeof document !== 'undefined') {
        var container = document.getElementById('container');
        if (container) {
            container.innerHTML = '';
            for (var i = 0; i < data.length; i++) {
                var div = document.createElement('div');
                div.innerHTML = '<span>' + data[i].name + '</span><span>' + data[i].value + '</span>';
                div.onclick = function(index) {
                    return function() {
                        alert('Clicked item ' + index);
                    };
                }(i);
                container.appendChild(div);
            }
        }
    }
}

// Main execution
if (typeof module === 'undefined') {
    // Browser environment
    console.log('Running in browser');
    
    // Test calculator
    console.log(calc(10, 5, 'add'));
    console.log(calc(10, 0, 'div'));
    
    // Test user data processing
    var userData = {
        name: '  john doe  ',
        email: 'JOHN@EXAMPLE.COM  ',
        age: '25'
    };
    var processed = processUserData(userData);
    console.log(processed);
    
    // Test score categorization
    var scores = [95, 87, 72, 45, 99];
    for (var i = 0; i < scores.length; i++) {
        console.log('Score ' + scores[i] + ': ' + categorizeScore(scores[i]));
    }
    
    // Test data processor
    var processor = new DataProcessor();
    processor.addNumber('10.5');
    processor.addString('hello');
    processor.addNumber('invalid');
    console.log('Average: ' + processor.calculateAverage());
    
    // Test batch processing
    processBatch([1, 2, 3, 4, 5]);
    console.log('Final counter: ' + counter);
    console.log('Results: ' + results);
    
    // Test async function
    fetchUserData(123, function(err, data) {
        if (err) {
            console.log('Error: ' + err);
        } else {
            console.log('User data:', data);
        }
    });
} else {
    // Node.js environment
    module.exports = {
        calc: calc,
        processUserData: processUserData,
        categorizeScore: categorizeScore,
        DataProcessor: DataProcessor
    };
}