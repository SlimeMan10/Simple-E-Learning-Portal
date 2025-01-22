"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var index_js_1 = require("./logInTypes/index.js");
window.addEventListener("load", init);
function init() {
    logInType();
}
function logInType() {
    id("student-btn").addEventListener("click", index_js_1.student);
    id("teacher-btn").addEventListener("click", index_js_1.teacher);
    id("create-btn").addEventListener("click", index_js_1.create);
}
function id(item) {
    var element = document.getElementById(item);
    if (!element) {
        throw new Error("Error getting element");
    }
    return element;
}
