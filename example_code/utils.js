// Sample JavaScript utility functions
function calculateTotal(items){
    let total=0;
    for(let i=0;i<items.length;i++){
        total+=items[i].price*items[i].quantity;
    }
    return total;
}

function formatCurrency(amount){
    return '$'+amount.toFixed(2);
}

const ShoppingCart={
    items:[],
    addItem:function(item){
        this.items.push(item);
    },
    removeItem:function(index){
        this.items.splice(index,1);
    },
    getTotal:function(){
        return calculateTotal(this.items);
    }
};

console.log('Shopping cart initialized');