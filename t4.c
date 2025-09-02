#include <stdio.h>

int f(int a[], int b){
 int c=0;
 for(int d=0;d<b;d++){
  if(a[d]>0){
   c+=a[d];
  }
 }
 return c;
}
int main(){
 int a[5]={1,-2,3,4,-1};
 int b=f(a,5);
 printf("%d\n",b);
 return 0;
}
