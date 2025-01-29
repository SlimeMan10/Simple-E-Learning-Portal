from flask import Flask, request, jsonify
import sqlite3
import os
import hashlib
import logging
import secrets

serverError = "An Internal Server Error Has Occurred"
logInError = "Username or Password was incorrect"
MAX_PERIODS = 7


app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.ERROR)

# Create a database connection
def __createConnection():
    try:
        conn = sqlite3.connect("./database/database.db")  # Ensure the database file exists
        cursor = conn.cursor()
        return conn, cursor
    except sqlite3.Error as e:
        raise Exception(f"Database connection failed: {str(e)}")

# Generate a salt
def __generateSalt():
    return os.urandom(16).hex()

# Hash a password with a given salt
def __hashPassword(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()

def __closeConnection(conn, cursor):
    if cursor:
        cursor.close()
    if conn:
        conn.close()

# Login route
#notes: use json raw to pass in
@app.route("/login", methods=["POST"])
def login():
    conn, cursor = None, None
    try:
        # Parse JSON from the request body
        data = request.json
        username = data.get("username")
        password = data.get("password")
        user_type = data.get("role")

        if not isinstance(username, str) or not isinstance(password, str) or not isinstance(user_type, str):
            return jsonify({"error": "wrong parameter types"})

        # Validate inputs
        if not all ([username, password, user_type]):
            return jsonify({"error": "Missing Parameter"}), 400
        # Connect to the database
        conn, cursor = __createConnection()
        user_type = user_type.capitalize()
        #verify role
        roleQuery = """
            SELECT 1
            FROM Roles
            WHERE role = ?
        """
        cursor.execute(roleQuery, [user_type])
        if not cursor.fetchone():
            return jsonify({"error": "role doesnt exist"}), 400

        # Query the database for the user's salt and hashed password
        query = "SELECT salt, hash FROM Users WHERE username = ?"
        cursor.execute(query, [username])
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": logInError}), 401

        # Retrieve the stored salt and hash
        stored_salt, stored_hash = user

        # Hash the input password using the stored salt
        input_hash = __hashPassword(password, stored_salt)

        # Compare the computed hash with the stored hash
        if not secrets.compare_digest(input_hash, stored_hash):
            return jsonify({"error": logInError}), 401

        # If login is successful
        return jsonify({"login": True, "message": "Login successful"}), 200

    except Exception as e:
        logging.error(f"Error during login: {e}")
        return jsonify({"error": serverError}), 500

    finally:
        __closeConnection(conn, cursor)

#TODO Admin Endpoints

@app.route("/addNewClass", methods=["POST"])
def addNewClass():
    data = request.json
    username = data.get("username")
    if not isinstance(username, str):
        return jsonify({"error": "parameter is wrong type"})
    if not username or not __checkRole(username, "admin"):
        return jsonify({"error": "Permission not granted"}), 400
    
    # Extract required parameters
    className = data.get("classname")
    description = data.get("description")
    teacher = data.get("teacher")  # Must be the teacher's name
    capacity = data.get("capacity")
    period = data.get("period")

    if not isinstance(className, str) or not isinstance(description, str) or not isinstance(teacher, str) or not isinstance(capacity, int) or not isinstance(period, int):
        return jsonify({"error": "parameters are of wrong types"})
    
    # Validate all required parameters
    if not all([className, description, teacher, capacity, period]):
        return jsonify({"error": "Missing parameters"}), 400

    conn, cursor = None, None  # Initialize connection and cursor
    try:
        conn, cursor = __createConnection()

        # Check if the teacher is free for the given period
        teacherQuery = """
            SELECT 1
            FROM Classes
            WHERE teacher = ? AND period = ?
        """
        cursor.execute(teacherQuery, [teacher, period])
        if cursor.fetchone():
            return jsonify({"error": "Teacher is already assigned for that period"}), 400

        # Add the new class to the database
        newClassQuery = """
            INSERT INTO Classes (className, classDescription, capacity, teacher, period) 
            VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(newClassQuery, [className, description, capacity, teacher, period])
        conn.commit()
        return jsonify({"message": "Class added successfully"}), 200
    except Exception as e:
        if conn:
            conn.rollback()  # Rollback transaction on error
        logging.error(f"Error during class addition: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and cursor:
            __closeConnection(conn, cursor)

#TODO: TEST
@app.route("/addStudentToClass", methods=["POST"])
def addStudentToClass():
    data = request.json
    username = data.get("username")
    student = data.get("student")
    classId = data.get("classId")
    if not all([isinstance(username, str), isinstance(student, str), isinstance(classId, int)]):
        return jsonify({"error": "parameter is wrong type"}), 400
    if not all([username, student, classId]):
        return jsonify({"error", "missing parameter"}), 400
    if not __checkRole(username, "admin"):
        return jsonify({"error", "Permission Denied"}), 400
    try:
        conn, cursor = __createConnection()
        #verify if the classId exists
        classIdQuery = """
            SELECT period, capacity
            FROM Classes
            WHERE classId = ?
        """
        cursor.execute(classIdQuery, [classId])
        period, capacity = cursor.fetchone()[0]
        if not period:
            return jsonify({"error", "class id doesn't exist"}), 400
        if capacity <= 0:
            return jsonify({"error": "no more space in class"}), 400
        #check if the student exists
        studentQuery = """
            SELECT 1
            FROM Users
            WHERE full_name = ?
        """
        cursor.execute(studentQuery, [student])
        if not cursor.fetchone():
            return jsonify({"error", "Student doesn't exist"}), 400
        #check if the students schedule fits it
        missingPeriods = __getMissingPeriods()
        if period not in missingPeriods:
            return jsonify({"error":"class doesnt fit schedule"}), 400
        #now lets insert the class into the students schedule
        insertClassQuery = """
            INSERT INTO StudentSchedule (student, classId, period) VALUES (?, ?, ?)
        """
        cursor.execute(insertClassQuery, [student, classId, period])
        #update the class capacity
        capacityQuery = """
            UPDATE Classes
            SET capacity = capacity - 1
            WHERE classId = ?
        """
        cursor.execute(capacityQuery, [classId])
        conn.commit()
        return jsonify({"status": "class added successfully"}), 200
    except Exception as e:
        if conn:
            conn.rollback()  # Roll back the transaction if an error occurs
        logging.error(f"Error during class deletion: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and cursor:
            __closeConnection(conn, cursor)

#TODO: check
@app.route("/deleteClass", methods=["DELETE"])
def deleteClass():
    data = request.json
    username = data.get("username")
    classId = data.get("classId")
    if not all([isinstance(username, str), isinstance(classId, int)]):
        return jsonify({"error": "parameters are wrong types"})
    if not all([username, classId]):
        return jsonify({"error": "missing parameter"}), 400
    if not __checkRole(username, "admin"):
        return jsonify({"error": "permission not granted"}), 400
    
    conn, cursor = None, None  # Initialize connection and cursor for safety
    try:
        # Check if the classId exists
        conn, cursor = __createConnection()
        classIdQuery = """
            SELECT 1
            FROM Classes
            WHERE id = ?
        """
        cursor.execute(classIdQuery, [classId])
        classIdResult = cursor.fetchone()
        if not classIdResult:
            return jsonify({"error": "class does not exist"}), 400
        
        # Delete the class
        deleteQuery = """
            DELETE FROM Classes
            WHERE id = ?
        """
        cursor.execute(deleteQuery, [classId])
        conn.commit()
        return jsonify({"message": "class deleted successfully"})
    except Exception as e:
        if conn:
            conn.rollback()  # Roll back the transaction if an error occurs
        logging.error(f"Error during class deletion: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and cursor:
            __closeConnection(conn, cursor)
        
#TODO: check
@app.route("/acceptClassDrop", methods=["POST"])
def acceptClassDrop():
    conn, cursor = None, None
    try:
        data = request.json
        username = data.get("username")
        studentName = data.get("studentName")
        classId = data.get("classId")
        if not isinstance(username, str) or not isinstance(studentName, str) or not isinstance(classId, int):
            return jsonify({"error": "missing parameter"})
        if not all([username, studentName, classId]):
            return jsonify({"error": "Missing required fields"}), 400

        if not __checkRole(username, "admin"):
            return jsonify({"error": "Permission denied"}), 403

        conn, cursor = __createConnection()
        conn.execute("BEGIN TRANSACTION")

        # Verify drop request exists
        cursor.execute("""
            SELECT 1 FROM DropRequests
            WHERE classId = ? AND student = ?
        """, [classId, studentName])
        if not cursor.fetchone():
            conn.rollback()
            return jsonify({"error": "Drop request not found"}), 404

        # Remove from ClassStudents
        cursor.execute("""
            DELETE FROM ClassStudents
            WHERE classId = ? AND student = ?
        """, [classId, studentName])

        # Update capacity
        cursor.execute("""
            UPDATE Classes 
            SET capacity = capacity + 1 
            WHERE id = ?
        """, [classId])

        # Remove from DropRequests
        cursor.execute("""
            DELETE FROM DropRequests 
            WHERE classId = ? AND student = ?
        """, [classId, studentName])

        conn.commit()
        return jsonify({"message": "Drop request processed"}), 200

    except Exception as e:
        logging.error(f"Drop error: {e}")
        conn.rollback() if conn else None
        return jsonify({"error": serverError}), 500
    finally:
        __closeConnection(conn, cursor)

#TODO: check
@app.route("/acceptAddClass", methods=["POST"])
def acceptAddClass():
    conn, cursor = None, None
    try:
        data = request.json
        username = data.get("username")
        studentName = data.get("student_name")
        classId = data.get("class_id")

        if not all ([
            isinstance(username, str),
            isinstance(studentName, str),
            isinstance(classId, int)
        ]):
            return jsonify({"error": "parameter is not the proper type"}), 400

        if not all([username, studentName, classId]):
            return jsonify({"error": "Missing required fields"}), 400

        if not __checkRole(username, "admin"):
            return jsonify({"error": "Permission denied"}), 403

        conn, cursor = __createConnection()
        conn.execute("BEGIN TRANSACTION")

        # Check capacity
        cursor.execute("SELECT capacity FROM Classes WHERE id = ?", [classId])
        capacity = cursor.fetchone()
        if not capacity or capacity[0] < 1:
            conn.rollback()
            return jsonify({"error": "Class is full"}), 400

        # Add to ClassStudents
        cursor.execute("""
            INSERT INTO ClassStudents (classId, student)
            VALUES (?, ?)
        """, [classId, studentName])

        # Update capacity
        cursor.execute("""
            UPDATE Classes 
            SET capacity = capacity - 1 
            WHERE id = ?
        """, [classId])

        # Remove from AddRequests
        cursor.execute("""
            DELETE FROM AddRequests 
            WHERE classId = ? AND student = ?
        """, [classId, studentName])

        conn.commit()
        return jsonify({"message": "Add request processed"}), 200

    except Exception as e:
        logging.error(f"Add error: {e}")
        conn.rollback() if conn else None
        return jsonify({"error": serverError}), 500
    finally:
        __closeConnection(conn, cursor)

#todo decline add
#TODO: check
@app.route("/declineAdd", methods=["DELETE"])
def declineAdd():
    data = request.json
    username = data.get("username")
    if not username or not __checkRole(username, "admin"):
        return jsonify({"error": "permission not granted"})
    addId = data.get("addId")
    classId = data.get("classId")
    student = data.get("student") #full name
    if not all([
        isinstance(addId, int),
        isinstance(classId, int),
        isinstance(student, str)
    ]):
        return jsonify({"error": "parameter not proper type"}), 400
    if not all([addId, classId, student]):
        return jsonify({"error": "missing parameter"}), 400
    try:
        conn, cursor = __createConnection()
        checkAddId = """
            SELECT 1
            FROM AddRequests
            WHERE id = ?
        """
        cursor.execute(checkAddId, [addId])
        if not cursor.fetchone():
            return jsonify({"error": "drop id is not valid"}), 400
        #lets verify the student exists now
        studentQuery = """
            SELECT 1
            FROM Users
            WHERE full_name = ?
        """
        cursor.execute(studentQuery, [student])
        if not cursor.fetchone():
            return jsonify({"error": "student doesnt exist"}), 400
        #now lets verify that the classId exists
        classIdQuery = """
            SELECT 1
            FROM Classes
            WHERE id = ?
        """
        cursor.execute(classIdQuery, [classId])
        if not cursor.fetchone():
            return jsonify({"error": "class does not exist"}), 400
        #Delete the student from the AddRequests and thats all
        declineQuery = """
            DELETE FROM AddRequests
            WHERE id = ?
        """
        cursor.execute(declineQuery, [addId])
        conn.commit()
        return jsonify({"message": "request removed"}), 200
    except Exception as e:
        logging.error(f"Add error: {e}")
        conn.rollback() if conn else None
        return jsonify({"error": serverError}), 500
    finally:
        __closeConnection(conn, cursor)

#todo decline drop
#TODO: check
@app.route("/declineDrop", methods=["POST"])
def declineDrop():
    data = request.json
    username = data.get("username")
    dropId = data.get("dropId")
    classId = data.get("classId")
    student = data.get("student") #full name
    if not all([
        isinstance(username, str),
        isinstance(dropId, int),
        isinstance(classId, int),
        isinstance(student, str)
    ]):
        return jsonify({"error": "parameter is wrong type"}), 400
    if not username or not __checkRole(username, "admin"):
        return jsonify({"error": "permission not granted"})
    if not all([dropId, classId, student]):
        return jsonify({"error": "missing parameter"}), 400
    try:
        conn, cursor = __createConnection()
        checkDropId = """
            SELECT 1
            FROM DropRequests
            WHERE id = ?
        """
        cursor.execute(checkDropId, [dropId])
        if not cursor.fetchone():
            return jsonify({"error": "drop id is not valid"}), 400
        #lets verify the student exists now
        studentQuery = """
            SELECT 1
            FROM Users
            WHERE full_name = ?
        """
        cursor.execute(studentQuery, [student])
        if not cursor.fetchone():
            return jsonify({"error": "student doesnt exist"}), 400
        #now lets verify that the classId exists
        classIdQuery = """
            SELECT 1
            FROM Classes
            WHERE id = ?
        """
        cursor.execute(classIdQuery, [classId])
        if not cursor.fetchone():
            return jsonify({"error": "class does not exist"}), 400
        #Delete the student from the AddRequests and thats all
        declineQuery = """
            DELETE FROM DropRequests
            WHERE id = ?
        """
        cursor.execute(declineQuery, [dropId])
        conn.commit()
        return jsonify({"message": "request removed"}), 200
    except Exception as e:
        logging.error(f"Add error: {e}")
        conn.rollback() if conn else None
        return jsonify({"error": serverError}), 500
    finally:
        __closeConnection(conn, cursor)

# Create new user (for admin)
#TODO: check
@app.route("/createUser", methods=["POST"])
def create_user():
    conn, cursor = None, None
    try:
        data = request.json
        adminUsername = data.get("username")
        newUsername = data.get("newUsername")
        userFullName = data.get("full_name")
        newPassword = data.get("newPassword")
        role = data.get("role")
        if not all([adminUsername, newUsername, userFullName, newPassword, role]):
            return jsonify({"error": "parameter is wrong type"}), 400
        if not __checkRole(adminUsername, "admin"):
            return jsonify({"error": "no username provides"}), 400

        # Validate the role
        if role not in ["admin", "student", "teacher"]:
            return jsonify({"error": "Invalid role"}), 400

        # Connect to the database
        salt = __generateSalt()
        hashedPassword = __hashPassword(newPassword, salt)
        conn, cursor = __createConnection()
        newUserQuery = "INSERT INTO Users (username, full_name, salt, hash, role) VALUES (?, ?, ?, ?, ?)"
        cursor.execute(newUserQuery, [newUsername, userFullName , salt, hashedPassword, role])
        conn.commit()
        return jsonify({"message": "User created successfully"}), 200

    except Exception as e:
        logging.error(f"Error during user creation: {e}")
        return jsonify({"error": serverError}), 500

    finally:
        __closeConnection(conn, cursor)

#TODO: check
@app.route("/deleteuser", methods=["DELETE"])
def delete():
    conn, cursor = None, None
    try:
        conn, cursor = __createConnection()
        data = request.json
        adminUsername = data.get("adminUsername")
        username = data.get("username")
        if not all([adminUsername, username]):
            return jsonify({"error": "parameter missing"}), 400
        if not __checkRole(adminUsername, "admin"):
            return jsonify({"error": "permission not granted"}), 400
        query = "DELETE FROM Users WHERE username = ?"
        cursor.execute(query, [username])
        conn.commit()
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        logging.error(f"Error during user deletion: {e}")
        return jsonify({"error": serverError}), 500
    finally:
        __closeConnection(conn, cursor)

#TODO: check
@app.route("/getDropClassRequest", methods=["GET"])
def get_drop_class_request():
    conn, cursor = None, None
    try:
        adminUsername = request.args.get("adminUsername")
        if not adminUsername:
            return jsonify({"error": "Admin must be signed in"}), 400
        if not __checkRole(adminUsername, "admin"):
            return jsonify({"error": "User is not an admin"}), 401

        conn, cursor = __createConnection()

        # Get all drop-class requests
        query = """
        SELECT c.id, c.className, c.classDescription, c.capacity, c.teacher, c.period, d.student 
        FROM DropClasses d
        JOIN Classes c ON d.classId = c.id
        """
        cursor.execute(query)
        classData = cursor.fetchall()

        # Format the data
        data = [
            {
                "classId": row[0],
                "className": row[1],
                "classDescription": row[2],
                "capacity": row[3],
                "teacher": row[4],
                "period": row[5],
                "student": row[6]
            }
            for row in classData
        ]

        return jsonify({"dropRequests": data}), 200
    except Exception as e:
        logging.error(f"Error fetching drop class requests: {e}")
        return jsonify({"error": serverError}), 500
    finally:
        __closeConnection(conn, cursor)

#TODO: check
@app.route("/getAddClassRequest", methods=["GET"])
def get_add_class_request():
    conn, cursor = None, None
    try:
        adminUsername = request.args.get("adminUsername")
        if not adminUsername:
            return jsonify({"error": "Admin must be signed in"}), 400
        if not __checkRole(adminUsername, "admin"):
            return jsonify({"error": "User is not an admin"}), 401

        conn, cursor = __createConnection()

        # Get all add-class requests
        query = """
        SELECT c.id, c.className, c.classDescription, c.capacity, c.teacher, c.period, a.student 
        FROM addClasses a
        JOIN Classes c ON a.classId = c.id
        """
        cursor.execute(query)
        classData = cursor.fetchall()

        # Format the data
        data = [
            {
                "classId": row[0],
                "className": row[1],
                "classDescription": row[2],
                "capacity": row[3],
                "teacher": row[4],
                "period": row[5],
                "student": row[6]
            }
            for row in classData
        ]

        return jsonify({"addRequests": data}), 200
    except Exception as e:
        logging.error(f"Error fetching add class requests: {e}")
        return jsonify({"error": serverError}), 500
    finally:
        __closeConnection(conn, cursor)

#todo: Teacher End Points

#TODO: check
@app.route("/getAllClassesTeacher", methods=["GET"])
def get_all_classes_teacher():
    conn, cursor = None, None
    try:
        conn, cursor = __createConnection()

        # Check if they are logged in
        data = request.args
        currentUser = data.get("username")
        if not currentUser:
            return jsonify({"error": "User is not logged in"}), 400

        # Verify if the user is a teacher
        if not __checkRole(currentUser, "teacher"):
            return jsonify({"error": "You are not a teacher"}), 403

        # Fetch classes assigned to the teacher
        query = """
        SELECT Classes.className, Classes.period 
        FROM TeacherSchedule
        JOIN Classes ON TeacherSchedule.classId = Classes.id
        WHERE TeacherSchedule.teacher = ?
        """
        cursor.execute(query, [currentUser])
        cursorData = cursor.fetchall()

        # Format the data
        returnData = [{"className": row[0], "period": row[1]} for row in cursorData]
        return jsonify({"Classes": returnData}), 200

    except Exception as e:
        logging.error(f"Error fetching teacher's classes: {e}")
        return jsonify({"error": serverError}), 500
    finally:
        __closeConnection(conn, cursor)

#must pass in username (has to be stored) and id (get when they click on the title)
#TODO: check
@app.route("/getStudentsInClass", methods=["GET"])
def get_students_in_class():
    conn, cursor = None, None
    try:
        currentUser = request.args.get("username")
        classId = request.args.get("id")
        
        if not all([currentUser, classId]):
            return jsonify({"error": "Missing parameters"}), 400

        if not __checkRole(currentUser, "teacher"):
            return jsonify({"error": "Permission denied"}), 403

        conn, cursor = __createConnection()

        # Verify teacher assignment
        cursor.execute("""
            SELECT 1 FROM TeacherSchedule 
            WHERE teacher = ? AND classId = ?
        """, [currentUser, classId])
        if not cursor.fetchone():
            return jsonify({"error": "Not assigned to class"}), 403

        # Get students
        cursor.execute("""
            SELECT student FROM ClassStudents 
            WHERE classId = ?
        """, [classId])
        
        return jsonify({
            "students": [row[0] for row in cursor.fetchall()]
        }), 200

    except Exception as e:
        logging.error(f"Student list error: {e}")
        return jsonify({"error": serverError}), 500
    finally:
        __closeConnection(conn, cursor)

#todo: Student end points

#can also be used to get all classes to drop
#TODO: check
@app.route("/getStudentClassInfo", methods=["GET"])
def studentClassInfo():
    data = request.args
    username = data.get("username")
    classId = data.get("classId")
    if not all([username, classId]):
        return jsonify({"error", "missing parameter"}), 400
    # Check if logged in and correct role
    if not __checkRole(username, "student"):
        return jsonify({"error": "Permission not granted"}), 403
    
    conn, cursor = None, None
    try:
        # Connect to the database
        conn, cursor = __createConnection()

        # Query for class information
        query = """
            SELECT className, classDescription, teacher
            FROM Classes
            WHERE id = ?
        """
        cursor.execute(query, [classId])
        classData = cursor.fetchone()

        # If the class does not exist
        if not classData:
            return jsonify({"error": "Class does not exist"}), 404

        # Format and return the response
        classForm = {
            "Class Name": classData[0],
            "Class Description": classData[1],
            "Teacher": classData[2]
        }
        return jsonify({"Data": classForm}), 200

    except Exception as e:
        logging.error(f"Error fetching class information for student: {e}")
        return jsonify({"error": serverError}), 500
    finally:
        __closeConnection(conn, cursor)

#TODO: check
@app.route("/sendDropRequest", methods=["POST"])
def sendDropRequest():
    conn, cursor = None, None
    try:
        data = request.json
        username = data.get("username")
        classId = data.get("classId")

        if not all([username, classId]):
            return jsonify({"error": "Missing required fields"}), 400

        if not __checkRole(username, "student"):
            return jsonify({"error": "Permission denied"}), 403

        conn, cursor = __createConnection()

        # Get full name
        cursor.execute("SELECT full_name FROM Users WHERE username = ?", [username])
        if not (full_name := cursor.fetchone()):
            return jsonify({"error": "User not found"}), 404

        # Check existing request
        cursor.execute("""
            SELECT 1 FROM DropRequests 
            WHERE classId = ? AND student = ?
        """, [classId, full_name[0]])
        if cursor.fetchone():
            return jsonify({"error": "Duplicate request"}), 409

        # Create request
        cursor.execute("""
            INSERT INTO DropRequests (classId, student)
            VALUES (?, ?)
        """, [classId, full_name[0]])

        conn.commit()
        return jsonify({"message": "Drop request submitted"}), 200

    except Exception as e:
        logging.error(f"Drop request error: {e}")
        return jsonify({"error": serverError}), 500
    finally:
        __closeConnection(conn, cursor)

#TODO: check
@app.route("/sendAddRequest", methods=["POST"])
def studentAddRequest():
    conn, cursor = None, None
    try:
        data = request.json

        # Validate input
        username = data.get('username')
        class_id = data.get("classId")
        if not all([username, class_id]):
            return jsonify({"error": "Missing username or class ID"}), 400

        if not __checkRole(username, "student"):
            return jsonify({"error": "Student access required"}), 403  # Proper 403 status

        conn, cursor = __createConnection()

        # Verify class existence and get details
        cursor.execute("""
            SELECT period, capacity, teacher 
            FROM Classes 
            WHERE id = ?
        """, [class_id])
        class_data = cursor.fetchone()
        if not class_data:
            return jsonify({"error": "Invalid class ID"}), 404

        class_period, capacity, teacher = class_data

        # Check class capacity
        cursor.execute("""
            SELECT COUNT(*) 
            FROM ClassStudents 
            WHERE classId = ?
        """, [class_id])
        enrolled = cursor.fetchone()[0]
        if enrolled >= capacity:
            return jsonify({"error": "Class is full"}), 409

        # Check student availability
        missing_periods = __getMissingPeriods(username)
        if class_period not in missing_periods:
            return jsonify({"error": f"Period {class_period} conflict"}), 409

        # Check existing requests
        cursor.execute("""
            SELECT 1 
            FROM AddRequests 
            WHERE classId = ? AND student = ?
        """, [class_id, username])  # Use username instead of full_name
        if cursor.fetchone():
            return jsonify({"error": "Duplicate add request"}), 409

        # Insert request
        cursor.execute("""
            INSERT INTO AddRequests (classId, student)
            VALUES (?, ?)
        """, [class_id, username])  # Store username instead of full_name
        
        conn.commit()
        return jsonify({"message": "Add request submitted"}), 200

    except Exception as e:
        logging.error(f"Add request error: {str(e)}", exc_info=True)
        if conn:
            conn.rollback()
        return jsonify({"error": "Internal server error"}), 500
    finally:
        __closeConnection(conn, cursor)

def __getMissingPeriods(username):
    conn, cursor = None, None
    try:
        conn, cursor = __createConnection()
        cursor.execute("""
            SELECT c.period 
            FROM ClassStudents cs
            JOIN Classes c ON cs.classId = c.id
            WHERE cs.student = (
                SELECT full_name FROM Users WHERE username = ?
            )
        """, [username])
        taken = {row[0] for row in cursor.fetchall()}
        return [p for p in range(1, MAX_PERIODS+1) if p not in taken]
    except Exception as e:
        logging.error(f"Period check error: {e}")
        return []
    finally:
        __closeConnection(conn, cursor)

#TODO: check
@app.route("/studentGetAvailableClasses", methods=["GET"])
def studentGetAvailableClasses():
    conn, cursor = None, None
    try:
        conn, cursor = __createConnection()

        # Check if the user is logged in
        data = request.args
        user = data.get('username')
        if not user:
            return jsonify({"error": "Username cannot be blank"}), 400
        if not __checkRole(user, "student"):
            return jsonify({"error": logInError}), 400

        # Fetch the periods the student is already enrolled in
        currentMissingPeriods = __getMissingPeriods(user)

        # If no missing periods, return an empty result
        if not currentMissingPeriods:
            return jsonify({"result": []}), 200

        # Query for available classes in the missing periods
        classQuery = """
        SELECT className, classDescription, teacher
        FROM Classes
        WHERE capacity > 0 AND period IN ({})
        """.format(",".join("?" for _ in currentMissingPeriods))  # Dynamically build placeholders
        cursor.execute(classQuery, currentMissingPeriods)
        classData = cursor.fetchall()

        # Format the result
        finalClassData = [
            {"Class Name": curr[0], "Class Description": curr[1], "Teacher": curr[2]}
            for curr in classData
        ]

        # Return the available classes
        return jsonify({"result": finalClassData}), 200

    except Exception as e:
        logging.error(f"Error fetching available classes: {e}")
        return jsonify({"error": serverError}), 500
    finally:
        __closeConnection(conn, cursor)

def __checkRole(username, roleCheck):
    conn, cursor = None, None
    try:
        username = username.capitalize()
        conn, cursor = __createConnection()
        query = "SELECT role FROM Users WHERE username = ?"
        cursor.execute(query, [username])
        user = cursor.fetchone()
        if not user:
            return None
        role = user[0]
        if role == roleCheck:
            return user
        return None
    except Exception as e:
        return None
    finally:
        __closeConnection(conn, cursor)

#TODO: check
@app.route("/changePassword", methods=["POST"])
def changePassword():
    data = request.json
    username = data.get('username') #username
    oldPassword = data.get("oldPassword")
    newPassword = data.get("newPassword")
    if not all([username, oldPassword, newPassword]):
        return jsonify({"error": "missing parameter"}), 400
    try:
        conn, cursor = __createConnection()
        #check if user exists
        userQuery = """
            SELECT 1
            FROM Users
            WHERE username = ?
        """
        cursor.execute(userQuery, [username])
        if not cursor.fetchone():
            return jsonify({"error", "user doesnt exist"}), 400
        #verify that oldpassword is valid
        passwordQuery = """
            SELECT salt, hash
            FROM Users
            WHERE username = ?
        """
        cursor.execute(passwordQuery, [username])
        salt, storedHash = cursor.fetchone()
        tempHash = __hashPassword(oldPassword, salt)
        if not secrets.compare_digest(tempHash, storedHash):
            return jsonify({"error": "invalid old password"}), 400
        newSalt = __generateSalt()
        newHash = __hashPassword(newPassword, newSalt)
        updatePasswordQuery = """
            UPDATE Users
            SET salt = ?, hash = ?
            WHERE username = ?
        """
        cursor.execute(updatePasswordQuery, [newSalt, newHash, username])
        conn.commit()

        return jsonify({"message": "password changed successfully"}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Error during password change: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if conn and cursor:
            __closeConnection(conn, cursor)

if __name__ == "__main__":
    app.run(debug=True)