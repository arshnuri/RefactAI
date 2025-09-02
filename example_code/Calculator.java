// Sample Java class for testing RefactAI
public class Calculator{
    private double result;
    
    public Calculator(){
        this.result=0.0;
    }
    
    public double add(double a,double b){
        result=a+b;
        return result;
    }
    
    public double subtract(double a,double b){
        result=a-b;
        return result;
    }
    
    public double multiply(double a,double b){
        result=a*b;
        return result;
    }
    
    public double divide(double a,double b){
        if(b!=0){
            result=a/b;
        }else{
            System.out.println("Error: Division by zero");
            result=0;
        }
        return result;
    }
    
    public double getResult(){
        return result;
    }
    
    public static void main(String[]args){
        Calculator calc=new Calculator();
        System.out.println("Addition: "+calc.add(10,5));
        System.out.println("Subtraction: "+calc.subtract(10,5));
        System.out.println("Multiplication: "+calc.multiply(10,5));
        System.out.println("Division: "+calc.divide(10,5));
    }
}