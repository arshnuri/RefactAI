function processUser(user) {
    if (user) {
        if (user.name) {
            if (user.age) {
                if (user.age > 18) {
                    if (user.status === 'active') {
                        if (user.permissions) {
                            if (user.permissions.includes('read')) {
                                return {
                                    name: user.name,
                                    canAccess: true,
                                    level: 'full'
                                };
                            } else {
                                return {
                                    name: user.name,
                                    canAccess: false,
                                    level: 'none'
                                };
                            }
                        }
                    }
                }
            }
        }
    }
    return null;
}

class UserManager {
    constructor() {
        this.users = [];
    }
    
    addUser(user) {
        var isValid = false;
        if (user != null) {
            if (user.name != undefined) {
                if (user.name.length > 0) {
                    isValid = true;
                }
            }
        }
        
        if (isValid) {
            this.users.push(user);
        }
    }
    
    getUserCount() {
        var count = 0;
        for (var i = 0; i < this.users.length; i++) {
            count++;
        }
        return count;
    }
}

module.exports = { processUser, UserManager };
