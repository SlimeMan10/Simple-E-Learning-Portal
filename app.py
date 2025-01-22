from flask import Flask, request, jsonify
import sqlite3
app = Flask(__name__)

def __createConnection():
    sqlite3.createConnection("./database/database.db")
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    return conn, cursor

@app.route("/login")
def login(username, password, type):
    if not username:
        raise Exception("Username is required")
    if not password:
        raise Exception("Password is required")
    if not type:
        raise Exception("Type is required")
    try:
        conn, cursor = __createConnection()
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        conn.close()
        