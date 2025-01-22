export function id(item: string): HTMLElement {
    const element: HTMLElement | null = document.getElementById(item);
    if(!element) {
        throw new Error("Element doesnt exist")
    }
    return element;
}

export function gen(item: string): HTMLElement {
    return document.createElement(item);
}

export function qs(item: string): HTMLElement {
    let element: HTMLElement | null = document.querySelector(item);
    if (!element) {
        throw new Error("No such element exists")
    }
    return element
}

export function qsa(item: string): NodeListOf<HTMLElement> {
    let element: NodeListOf<HTMLElement> | null = document.querySelectorAll(item);
    if (!element) {
        throw new Error("No such element exists")
    }
    return element
}