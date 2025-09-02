function f(a){
 let b=0;
 for(let c=0;c<a.length;c++){
  if(a[c]>0){
   b+=a[c];
  }
 }
 return b;
}
let d=[1,-2,3,4,-1];
let e=f(d);
console.log(e);
