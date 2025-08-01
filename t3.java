public class Calculator {
    private int value;
    
    public Calculator() {
        this.value = 0;
    }
    
    public int processNumbers(int a, int b, String operation) {
        if (operation != null) {
            if (operation.equals("add")) {
                if (a > 0) {
                    if (b > 0) {
                        if (a + b < 100) {
                            return a + b;
                        } else {
                            return 100;
                        }
                    } else {
                        return a;
                    }
                } else {
                    return b;
                }
            } else if (operation.equals("multiply")) {
                if (a != 0) {
                    if (b != 0) {
                        return a * b;
                    }
                }
                return 0;
            }
        }
        return -1;
    }
    
    public boolean validateInput(String input) {
        boolean isValid = false;
        if (input != null) {
            if (input.length() > 0) {
                if (!input.trim().isEmpty()) {
                    if (input.matches("\\d+")) {
                        isValid = true;
                    }
                }
            }
        }
        return isValid;
    }
    
    public void setValue(int newValue) {
        if (newValue >= 0) {
            if (newValue <= 1000) {
                if (newValue != this.value) {
                    this.value = newValue;
                }
            }
        }
    }
    
    public int getValue() {
        return this.value;
    }
}
