"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.id = id;
exports.gen = gen;
exports.qs = qs;
exports.qsa = qsa;
function id(item) {
    var element = document.getElementById(item);
    if (!element) {
        throw new Error("Element doesnt exist");
    }
    return element;
}
function gen(item) {
    return document.createElement(item);
}
function qs(item) {
    var element = document.querySelector(item);
    if (!element) {
        throw new Error("No such element exists");
    }
    return element;
}
function qsa(item) {
    var element = document.querySelectorAll(item);
    if (!element) {
        throw new Error("No such element exists");
    }
    return element;
}
