"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.student = student;
exports.teacher = teacher;
exports.create = create;
var index_js_1 = require("../general/index.js");
function student() {
    //unhide everything that is hidden
    var data = (0, index_js_1.qsa)("teacher-stuff");
    data.forEach(function (item) {
        item.classList.remove("hidden");
    });
    (0, index_js_1.id)("log-in-option").classList.add("hidden");
}
function teacher() {
}
function create() {
}
