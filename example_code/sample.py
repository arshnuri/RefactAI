# Sample Python code for testing RefactAI
import os
import sys

def calculate_area(length,width):
    result=length*width
    return result

class Rectangle:
    def __init__(self,l,w):
        self.length=l
        self.width=w
    def get_area(self):
        return calculate_area(self.length,self.width)
    def get_perimeter(self):
        return 2*(self.length+self.width)

if __name__=='__main__':
    rect=Rectangle(10,5)
    print('Area:',rect.get_area())
    print('Perimeter:',rect.get_perimeter())