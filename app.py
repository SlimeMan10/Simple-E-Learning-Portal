from flask import Flask, request, jsonify
import sqlite3
import os
import hashlib
import logging

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
@app.route("/login", methods=["POST"])
def login():
    conn, cursor = None, None
    try:
        # Parse JSON from the request body
        data = request.json
        username = data.get("username")
        password = data.get("password")
        user_type = data.get("type")

        # Validate inputs
        if not username:
            return jsonify({"error": "Username is required"}), 400
        if not password:
            return jsonify({"error": "Password is required"}), 400
        if not user_type:
            return jsonify({"error": "Type is required"}), 400

        # Connect to the database
        conn, cursor = __createConnection()

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
        if input_hash != stored_hash:
            return jsonify({"error": logInError}), 401

        # If login is successful
        return jsonify({"login": True, "message": "Login successful"}), 200

    except Exception as e:
        logging.error(f"Error during login: {e}")
        return jsonify({"error": serverError}), 500

    finally:
        __closeConnection(conn, cursor)

#TODO: Admin Endpoints
@app.route("/acceptClassDrop", methods=["POST"])
def acceptClassDrop():
    conn, cursor = None, None
    try:
        # Parse request data
        data = request.json
        username = data.get("username")
        studentName = data.get("studentName")
        classId = data.get("classId")

        # Validate inputs
        if not username:
            return jsonify({"error": "User did not provide username"}), 400
        if not __checkRole(username, "admin"):
            return jsonify({"error": "User is not an admin"}), 403
        if not studentName:
            return jsonify({"error": "Student name not provided"}), 400
        if not classId:
            return jsonify({"error": "Class ID not provided"}), 400

        # Connect to the database
        conn, cursor = __createConnection()

        # Verify the drop request exists
        dropRequestQuery = """
            SELECT 1 FROM dropClasses
            WHERE classId = ? AND student = ?
        """
        cursor.execute(dropRequestQuery, [classId, studentName])
        dropRequestExists = cursor.fetchone()
        if not dropRequestExists:
            return jsonify({"error": "Drop request not found"}), 404

        # Remove the student from StudentSchedule
        removeStudentQuery = """
            DELETE FROM StudentSchedule
            WHERE student = ? AND classId = ?
        """
        cursor.execute(removeStudentQuery, [studentName, classId])

        # Update capacity in the Classes table
        updateCapacityQuery = """
            UPDATE Classes
            SET capacity = capacity + 1
            WHERE id = ?
        """
        cursor.execute(updateCapacityQuery, [classId])

        # Delete the drop request from dropClasses
        deleteDropRequestQuery = """
            DELETE FROM dropClasses
            WHERE classId = ? AND student = ?
        """
        cursor.execute(deleteDropRequestQuery, [classId, studentName])

        # Commit changes
        conn.commit()

        return jsonify({"message": "Class drop request successfully processed"}), 200

    except Exception as e:
        logging.error(f"Error processing class drop request: {e}")
        return jsonify({"error": serverError}), 500
    finally:
        __closeConnection(conn, cursor)

#todo accept add
@app.route("/acceptAddClass", methods=["POST"])
def acceptAddClass():
    conn, cursor = None, None
    try:
        # Parse request data
        data = request.json
        user = data.get("username")
        studentName = data.get("student_name")
        classId = data.get("class_id")

        # Validate inputs
        if not user:
            return jsonify({"error": "User is not logged in"}), 400
        if not __checkRole(user, "admin"):
            return jsonify({"error": "Permission not granted"}), 403
        if not studentName:
            return jsonify({"error": "Student name not provided"}), 400
        if not classId:
            return jsonify({"error": "Class ID not provided"}), 400

        # Connect to the database
        conn, cursor = __createConnection()

        # Verify the class has available capacity
        spaceQuery = """
            SELECT capacity
            FROM Classes
            WHERE id = ? AND capacity > 0
        """
        cursor.execute(spaceQuery, [classId])
        capacity = cursor.fetchone()
        if not capacity:
            return jsonify({"error": "Class capacity has been reached"}), 400

        # Insert the student-class relationship into ClassStudents
        insertQuery = """
            INSERT INTO ClassStudents (classId, student)
            VALUES (?, ?)
        """
        cursor.execute(insertQuery, [classId, studentName])

        # Decrease the class capacity
        updateCapacityQuery = """
            UPDATE Classes
            SET capacity = capacity - 1
            WHERE id = ?
        """
        cursor.execute(updateCapacityQuery, [classId])

        # Remove the request from addClasses (AddRequests table)
        removeQuery = """
            DELETE FROM addClasses
            WHERE classId = ? AND student = ?
        """
        cursor.execute(removeQuery, [classId, studentName])

        # Commit the changes
        conn.commit()

        return jsonify({"status": "Add request successfully processed"}), 200

    except Exception as e:
        # Rollback in case of an error
        if conn:
            conn.rollback()
        logging.error(f"Error processing add class request: {e}")
        return jsonify({"error": serverError}), 500

    finally:
        __closeConnection(conn, cursor)

#todo decline add

#todo decline drop

#todo add role

# Create new user (for admin)
@app.route("/createUser", methods=["POST"])
def create_user():
    conn, cursor = None, None
    try:
        data = request.json
        adminUsername = data.get("username")
        if not adminUsername:
            return jsonify({"error": "no username provides"}), 400
        if not __checkRole(adminUsername, "admin"):
            return jsonify({"error": "Permission not granted"}), 400
        # Now we can create the new user
        newUsername = data.get("newUsername")
        userFullName = data.get("full_name")
        newPassword = data.get("newPassword")
        role = data.get("role")
        if not newUsername:
            return jsonify({"error": "New username is required"}), 400
        if not userFullName:
            return jsonify({"error": "Users name is required"}), 400
        if not newPassword:
            return jsonify({"error": "New password is required"}), 400

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

@app.route("/deleteuser", methods=["DELETE"])
def delete():
    conn, cursor = None, None
    try:
        conn, cursor = __createConnection()
        data = request.json
        adminUsername = data.get("adminUsername")
        if not adminUsername:
            return jsonify({"error": "Admin username is required"}), 400
        adminUser = __checkRole(adminUsername, "admin")
        if not adminUser:
            return jsonify({"error": "Admin authentication failed"}), 401
        username = data.get("username")
        if not username:
            return jsonify({"error": "Username is required"}), 400
        query = "DELETE FROM Users WHERE username = ?"
        cursor.execute(query, [username])
        conn.commit()
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        logging.error(f"Error during user deletion: {e}")
        return jsonify({"error": serverError}), 500
    finally:
        __closeConnection(conn, cursor)

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
        FROM dropClasses d
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

#TODO: Teacher End Points

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
@app.route("/getStudentsInClass", methods=["GET"])
def get_students_in_class():
    conn, cursor = None, None
    try:
        conn, cursor = __createConnection()

        # Parse query parameters
        data = request.args
        currentUser = data.get("username")
        classId = data.get("id")

        # Validate inputs
        if not currentUser:
            return jsonify({"error": "User is not logged in"}), 400
        if not classId:
            return jsonify({"error": "Class ID is required"}), 400

        # Check if the user is a teacher
        if not __checkRole(currentUser, "teacher"):
            return jsonify({"error": "You are not authorized to access this resource"}), 403

        # Verify if the teacher is assigned to the class
        validation_query = """
        SELECT id FROM TeacherSchedule 
        WHERE teacher = ? AND classId = ?
        """
        cursor.execute(validation_query, [currentUser, classId])
        assignment = cursor.fetchone()
        if not assignment:
            return jsonify({"error": "You are not assigned to this class"}), 403

        # Fetch students in the class
        student_query = """
        SELECT student 
        FROM Classes 
        WHERE id = ?
        """
        cursor.execute(student_query, [classId])
        students = cursor.fetchall()

        # Format the result
        result = [{"Student Name": row[0]} for row in students]
        return jsonify({"Students": result}), 200

    except Exception as e:
        logging.error(f"Error fetching students in class: {e}")
        return jsonify({"error": serverError}), 500
    finally:
        __closeConnection(conn, cursor)

#TODO: Student end points

#TODO make endpoint to view classes taken (view all classes)
@app.route("/studentGetAllClasses", methods=["GET"])
def student_get_all_classes():
    conn, cursor = None, None
    try:
        conn, cursor = __createConnection()
        
        # Validate username and role
        data = request.args
        username = data.get("username")
        if not username:
            return jsonify({"error": "User is not signed in"}), 400
        if not __checkRole(username, "student"):
            return jsonify({"error": "User is not a student"}), 403

        # Fetch all classes for the student
        classes_query = """
        SELECT c.className, c.classDescription, c.teacher 
        FROM StudentSchedule ss
        JOIN Classes c ON ss.classId = c.id
        JOIN Users u ON ss.student = u.full_name
        WHERE u.username = ?
        """
        cursor.execute(classes_query, [username])
        classes = cursor.fetchall()

        # Format the result
        if not classes:
            return jsonify({"Data": [], "message": "No classes found"}), 200

        class_list = [{
            "Class Name": class_data[0],
            "Class Description": class_data[1],
            "Teacher": class_data[2]
        } for class_data in classes]

        return jsonify({"Data": class_list}), 200
    except Exception as e:
        logging.error(f"Error fetching classes for student: {e}")
        return jsonify({"error": serverError}), 500
    finally:
        __closeConnection(conn, cursor)

#Todo if they select the class it should give the teacher and class description (clicking card)

#TODO view all classes to drop

#TODO send drop request


@app.route("/studentAddRequest", methods=["POST"])
def studentAddRequest():
    conn, cursor = None, None
    try:
        data = request.json

        # Validate username
        user = data.get('username')
        if not user:
            return jsonify({"error": "User not logged in"}), 400
        if not __checkRole(user, "student"):
            return jsonify({"error": logInError}), 400

        # Validate classId
        classId = data.get("classId")
        if not classId:
            return jsonify({"error": "classId is required"}), 400

        conn, cursor = __createConnection()

        # Check the period for the given classId
        query = """
            SELECT period FROM Classes WHERE id = ?
        """
        cursor.execute(query, [classId])
        classData = cursor.fetchone()
        if not classData:
            return jsonify({"error": "Invalid classId"}), 400
        classPeriod = classData[0]

        # Get missing periods for the student
        missingPeriods = __getMissingPeriods(user)  # Ensure this helper function is implemented
        if classPeriod not in missingPeriods:
            return jsonify({"error": "Period conflict"}), 400

        # Fetch full_name for the user
        nameQuery = """
            SELECT full_name FROM Users WHERE username = ?
        """
        cursor.execute(nameQuery, [user])
        full_name_data = cursor.fetchone()
        if not full_name_data:
            return jsonify({"error": "User not found"}), 400
        full_name = full_name_data[0]

        # Insert add request into the addClasses table
        addQuery = """
            INSERT INTO addClasses (classId, student) VALUES (?, ?)
        """
        cursor.execute(addQuery, [classId, full_name])
        conn.commit()

        return jsonify({"message": "Add Request Successful"}), 200
    except Exception as e:
        logging.error(f"Error processing add request: {e}")
        return jsonify({"error": serverError}), 500
    finally:
        __closeConnection(conn, cursor)

def __getMissingPeriods(user):
    conn, cursor = None, None
    try:
        conn, cursor = __createConnection()
        query = """
            SELECT period 
            FROM StudentSchedule 
            JOIN Users ON Users.full_name = StudentSchedule.student 
            WHERE Users.username = ?
            """
        cursor.execute(query, [user])
        queryData = cursor.fetchall()
        enrolledPeriods = [row[0] for row in queryData]
        periods = list(range(1, MAX_PERIODS + 1)) 
        currentMissingPeriods = [p for p in periods if p not in enrolledPeriods]
        return currentMissingPeriods
    except Exception as e:
        logging.error(f"Error fetching students in class: {e}")
        return jsonify({"error": serverError}), 500
    finally:
        __closeConnection(conn, cursor)

#Method: Gets the classes available for the student that will fit their schedule
#Exceptions: returns error codes if username is blank, not the right role, or a server error
#Returns: returns a json but if all goes well it will return the class name, description, and teacher
        #for all classes available to the student
#Parameters: username - users username
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

if __name__ == "__main__":
    app.run(debug=True)
