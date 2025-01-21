window.addEventListener("load", init)

function init(): void {
    id("login-btn").addEventListener("click", login)
    id("clear-btn").addEventListener("click", clear)
}

function id(item: string): HTMLElement {
    const element = document.getElementById(item);
    if (!element) {
        throw new Error(`Element with id ${item} not found`);
    }
    return element;
}

function gen(item: string): HTMLElement {
    return document.createElement(item);
}

function login(event: Event): void {
    event.preventDefault()
    let username = (id('username') as HTMLInputElement).value;
    let password = (id("password") as HTMLInputElement).value;
    if (!username ||!password) {
        console.error("Username and password cannot be empty!");
        return;
    }
    if (username.trim() === "" || password.trim() === "") {
        console.error("Username and password cannot contain only whitespace!");
        return;
    }
}

function clear(): void {
    let username = (id('username') as HTMLInputElement).value;
    let password = (id("password") as HTMLInputElement).value;
    if (username) {
        (id("username") as HTMLInputElement).value = "";
    }
    if (password) {
        (id("password") as HTMLInputElement).value = "";
    }
    console.log("Cleared!");
}