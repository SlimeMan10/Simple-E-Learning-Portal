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

async function login(event: Event): Promise<void> {
    event.preventDefault();
    let username = (id('username') as HTMLInputElement).value;
    let password = (id("password") as HTMLInputElement).value;

    if (!username || !password) {
        console.error("Username and password cannot be empty!");
        return;
    }
    if (username.trim() === "" || password.trim() === "") {
        console.error("Username and password cannot contain only whitespace!");
        return;
    }

    try {
        // Send a POST request to authenticate the user
        const response: Response = await fetch("/api/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ username, password }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        console.log("Login successful!");

        // Redirect to the dashboard
        window.location.href = "/dashboard"; // Update with the correct dashboard URL

        // Optionally, clear the input fields
        clear();
    } catch (error) {
        console.error("An error occurred:", error);
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