import { id, qsa } from "../general/index.js"

export function student(): void {
    //unhide everything that is hidden
    let data = qsa("teacher-stuff")
    data.forEach((item) => {
        item.classList.remove("hidden")
    });
    (id("log-in-option") as HTMLElement).classList.add("hidden")
}

export function teacher(): void {
    
}

export function create(): void {
    
}