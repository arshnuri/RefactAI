// Java Test Sample - Unrefactored Code with Multiple Quality Issues
// This code demonstrates various refactoring opportunities

import java.util.*;
import java.io.*;
import java.text.SimpleDateFormat;

// Poor naming and code duplication
public class TestSamplesForRefactoring {
    
    // Magic numbers and poor method design
    public static String calc(double x, double y, String op) {
        if (op.equals("add")) {
            return String.valueOf(x + y);
        } else if (op.equals("sub")) {
            return String.valueOf(x - y);
        } else if (op.equals("mul")) {
            return String.valueOf(x * y);
        } else if (op.equals("div")) {
            if (y != 0) {
                return String.valueOf(x / y);
            } else {
                return "Error: Division by zero";
            }
        } else {
            return "Invalid operation";
        }
    }
    
    // Long method with multiple responsibilities
    public static Map<String, Object> processUserData(Map<String, String> data) {
        // Validation
        if (data == null) {
            System.out.println("No data provided");
            return null;
        }
        
        if (data.isEmpty()) {
            System.out.println("Data is empty");
            return null;
        }
        
        // Processing
        Map<String, Object> result = new HashMap<>();
        
        if (data.containsKey("name")) {
            String name = data.get("name").trim();
            String[] words = name.split(" ");
            StringBuilder titleCase = new StringBuilder();
            for (String word : words) {
                if (word.length() > 0) {
                    titleCase.append(Character.toUpperCase(word.charAt(0)));
                    if (word.length() > 1) {
                        titleCase.append(word.substring(1).toLowerCase());
                    }
                    titleCase.append(" ");
                }
            }
            result.put("name", titleCase.toString().trim());
        }
        
        if (data.containsKey("email")) {
            result.put("email", data.get("email").toLowerCase().trim());
        }
        
        if (data.containsKey("age")) {
            try {
                result.put("age", Integer.parseInt(data.get("age")));
            } catch (NumberFormatException e) {
                System.out.println("Invalid age format");
                result.put("age", null);
            }
        }
        
        // Logging
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        String timestamp = sdf.format(new Date());
        String logEntry = "[" + timestamp + "] Processed user: " + result.getOrDefault("name", "Unknown");
        System.out.println(logEntry);
        
        // File operations
        try {
            FileWriter fw = new FileWriter("user_log.txt", true);
            fw.write(logEntry + "\n");
            fw.close();
        } catch (IOException e) {
            System.out.println("Failed to write to log file");
        }
        
        return result;
    }
    
    // Nested conditions and magic numbers
    public static String categorizeScore(int score) {
        if (score >= 90) {
            if (score >= 95) {
                if (score >= 98) {
                    return "Exceptional";
                } else {
                    return "Excellent";
                }
            } else {
                return "Very Good";
            }
        } else if (score >= 80) {
            if (score >= 85) {
                return "Good";
            } else {
                return "Above Average";
            }
        } else if (score >= 70) {
            return "Average";
        } else if (score >= 60) {
            return "Below Average";
        } else {
            return "Poor";
        }
    }
    
    // Code duplication and poor error handling
    static class DataProcessor {
        private List<Object> data;
        
        public DataProcessor() {
            this.data = new ArrayList<>();
        }
        
        public void addNumber(String num) {
            try {
                this.data.add(Double.parseDouble(num));
            } catch (Exception e) {
                System.out.println("Error adding number");
            }
        }
        
        public void addString(String text) {
            try {
                this.data.add(text);
            } catch (Exception e) {
                System.out.println("Error adding string");
            }
        }
        
        public List<Double> getNumbers() {
            List<Double> numbers = new ArrayList<>();
            for (Object item : this.data) {
                if (item instanceof Double) {
                    numbers.add((Double) item);
                }
            }
            return numbers;
        }
        
        public List<String> getStrings() {
            List<String> strings = new ArrayList<>();
            for (Object item : this.data) {
                if (item instanceof String) {
                    strings.add((String) item);
                }
            }
            return strings;
        }
        
        public double calculateAverage() {
            List<Double> numbers = getNumbers();
            if (numbers.size() == 0) {
                return 0.0;
            }
            double total = 0.0;
            for (Double num : numbers) {
                total += num;
            }
            return total / numbers.size();
        }
    }
    
    // Global-like static variables and poor structure
    private static int counter = 0;
    private static List<Integer> results = new ArrayList<>();
    
    public static void incrementCounter() {
        counter++;
    }
    
    public static void addResult(int value) {
        results.add(value);
    }
    
    public static void processBatch(int[] items) {
        for (int item : items) {
            incrementCounter();
            int processed = item * 2 + 1;
            addResult(processed);
            System.out.println("Processed item " + counter + ": " + processed);
        }
    }
    
    // Poor exception handling and resource management
    public static String readFileContent(String filename) {
        try {
            FileReader fr = new FileReader(filename);
            BufferedReader br = new BufferedReader(fr);
            StringBuilder content = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) {
                content.append(line).append("\n");
            }
            br.close();
            fr.close();
            return content.toString();
        } catch (Exception e) {
            System.out.println("Error reading file: " + e.getMessage());
            return null;
        }
    }
    
    // Poor class design with tight coupling
    static class UserManager {
        private List<Map<String, Object>> users;
        
        public UserManager() {
            this.users = new ArrayList<>();
        }
        
        public void addUser(String name, String email, int age) {
            Map<String, Object> user = new HashMap<>();
            user.put("name", name);
            user.put("email", email);
            user.put("age", age);
            user.put("id", users.size() + 1);
            users.add(user);
            
            // Tight coupling - directly writing to file
            try {
                FileWriter fw = new FileWriter("users.txt", true);
                fw.write("User added: " + name + " (" + email + ")\n");
                fw.close();
            } catch (IOException e) {
                System.out.println("Failed to log user addition");
            }
            
            // Tight coupling - directly printing
            System.out.println("Added user: " + name);
        }
        
        public Map<String, Object> findUserByEmail(String email) {
            for (Map<String, Object> user : users) {
                if (user.get("email").equals(email)) {
                    return user;
                }
            }
            return null;
        }
        
        public void printAllUsers() {
            System.out.println("All users:");
            for (Map<String, Object> user : users) {
                System.out.println("- " + user.get("name") + " (" + user.get("email") + ")");
            }
        }
    }
    
    // Main method with poor practices
    public static void main(String[] args) {
        // Test calculator
        System.out.println(calc(10, 5, "add"));
        System.out.println(calc(10, 0, "div"));
        
        // Test user data processing
        Map<String, String> userData = new HashMap<>();
        userData.put("name", "  john doe  ");
        userData.put("email", "JOHN@EXAMPLE.COM  ");
        userData.put("age", "25");
        Map<String, Object> processed = processUserData(userData);
        System.out.println(processed);
        
        // Test score categorization
        int[] scores = {95, 87, 72, 45, 99};
        for (int score : scores) {
            System.out.println("Score " + score + ": " + categorizeScore(score));
        }
        
        // Test data processor
        DataProcessor processor = new DataProcessor();
        processor.addNumber("10.5");
        processor.addString("hello");
        processor.addNumber("invalid");
        System.out.println("Average: " + processor.calculateAverage());
        
        // Test batch processing
        int[] items = {1, 2, 3, 4, 5};
        processBatch(items);
        System.out.println("Final counter: " + counter);
        System.out.println("Results: " + results);
        
        // Test user manager
        UserManager userManager = new UserManager();
        userManager.addUser("Alice Smith", "alice@example.com", 30);
        userManager.addUser("Bob Johnson", "bob@example.com", 25);
        userManager.printAllUsers();
        
        Map<String, Object> foundUser = userManager.findUserByEmail("alice@example.com");
        if (foundUser != null) {
            System.out.println("Found user: " + foundUser.get("name"));
        }
        
        // Test file reading
        String content = readFileContent("test.txt");
        if (content != null) {
            System.out.println("File content length: " + content.length());
        }
    }
}