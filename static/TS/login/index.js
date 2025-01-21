window.addEventListener("load", init);
function init() {
    id("login-btn").addEventListener("click", login);
    id("clear-btn").addEventListener("click", clear);
}
function id(item) {
    var element = document.getElementById(item);
    if (!element) {
        throw new Error("Element with id ".concat(item, " not found"));
    }
    return element;
}
function gen(item) {
    return document.createElement(item);
}
function login(event) {
    event.preventDefault();
    var username = id('username').value;
    var password = id("password").value;
    if (!username || !password) {
        console.error("Username and password cannot be empty!");
        return;
    }
    if (username.trim() === "" || password.trim() === "") {
        console.error("Username and password cannot contain only whitespace!");
        return;
    }
}
function clear() {
    var username = id('username').value;
    var password = id("password").value;
    if (username) {
        id("username").value = "";
    }
    if (password) {
        id("password").value = "";
    }
    console.log("Cleared!");
}
