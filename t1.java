public class t1{
 public static void main(String[] args){
  int[] a = {1,-2,3,4,-1};
  int b = 0;
  for(int c=0;c<a.length;c++){
   if(a[c]>0){
    b+=a[c];
   }
  }
  
  System.out.println(b);
 }
}
