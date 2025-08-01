#include <iostream>
#include <string>
#include <vector>

class DataProcessor {
private:
    std::vector<int> data;
    
public:
    DataProcessor() {}
    
    int processValue(int input, std::string mode) {
        if (input > 0) {
            if (mode == "double") {
                if (input < 100) {
                    if (input % 2 == 0) {
                        if (input > 10) {
                            return input * 2 + 5;
                        } else {
                            return input * 2;
                        }
                    } else {
                        return input * 2 - 1;
                    }
                } else {
                    return 200;
                }
            } else if (mode == "triple") {
                if (input < 50) {
                    return input * 3;
                }
            }
        }
        return 0;
    }
    
    bool validateData(const std::vector<int>& inputData) {
        bool isValid = false;
        if (!inputData.empty()) {
            if (inputData.size() > 0) {
                if (inputData.size() < 1000) {
                    bool allPositive = true;
                    for (int i = 0; i < inputData.size(); i++) {
                        if (inputData[i] <= 0) {
                            allPositive = false;
                            break;
                        }
                    }
                    if (allPositive) {
                        isValid = true;
                    }
                }
            }
        }
        return isValid;
    }
    
    void addData(int value) {
        if (value > 0) {
            if (value < 10000) {
                if (data.size() < 100) {
                    data.push_back(value);
                }
            }
        }
    }
};
