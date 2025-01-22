import { student, teacher, create } from "./logInTypes/index.js"

window.addEventListener("load", init)

function init(): void {
    logInType();
}

function logInType(): void {
    (id("student-btn") as HTMLButtonElement).addEventListener("click", student);
    (id("teacher-btn") as HTMLButtonElement).addEventListener("click", teacher);
    (id("create-btn") as HTMLButtonElement).addEventListener("click", create);
}

function id(item: string): HTMLElement {
    const element: HTMLElement | null = document.getElementById(item);
    if (!element) {
        throw new Error("Error getting element")
    }
    return element
}

