# Flask API Documentation

## Introduction
This documentation describes the endpoints for the Flask application managing users, classes, and requests (add/drop). It provides role-based permissions and CRUD operations for admins, teachers, and students.

---

## Endpoints

### Authentication
#### 1. **Login**
- **Endpoint**: `/login`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "username": "string",
    "password": "string",
    "type": "string"
  }
  ```
- **Response**:
  - Success: `200 OK`
    ```json
    {
      "login": true,
      "message": "Login successful"
    }
    ```
  - Failure: `401 Unauthorized` or `500 Internal Server Error`

---

### Admin Endpoints
#### 2. **Add New Class**
- **Endpoint**: `/addNewClass`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "username": "string",
    "classname": "string",
    "description": "string",
    "teacher": "string",
    "capacity": "int",
    "period": "int"
  }
  ```
- **Response**:
  - Success: `200 OK`
    ```json
    { "message": "Class added successfully" }
    ```
  - Failure: `400 Bad Request` or `500 Internal Server Error`

#### 3. **Delete Class**
- **Endpoint**: `/deleteClass`
- **Method**: `DELETE`
- **Request Body**:
  ```json
  {
    "username": "string",
    "classId": "int"
  }
  ```
- **Response**:
  - Success: `200 OK`
    ```json
    { "message": "Class deleted successfully" }
    ```
  - Failure: `400 Bad Request` or `500 Internal Server Error`

#### 4. **Accept Class Drop Request**
- **Endpoint**: `/acceptClassDrop`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "username": "string",
    "studentName": "string",
    "classId": "int"
  }
  ```
- **Response**:
  - Success: `200 OK`
    ```json
    { "message": "Drop request processed" }
    ```
  - Failure: `400 Bad Request` or `500 Internal Server Error`

#### 5. **Accept Add Class Request**
- **Endpoint**: `/acceptAddClass`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "username": "string",
    "student_name": "string",
    "class_id": "int"
  }
  ```
- **Response**:
  - Success: `200 OK`
    ```json
    { "message": "Add request processed" }
    ```
  - Failure: `400 Bad Request` or `500 Internal Server Error`

#### 6. **Decline Add Request**
- **Endpoint**: `/declineAdd`
- **Method**: `DELETE`
- **Request Body**:
  ```json
  {
    "username": "string",
    "addId": "int",
    "classId": "int",
    "student": "string"
  }
  ```
- **Response**:
  - Success: `200 OK`
    ```json
    { "message": "Request removed" }
    ```
  - Failure: `400 Bad Request` or `500 Internal Server Error`

#### 7. **Decline Drop Request**
- **Endpoint**: `/declineDrop`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "username": "string",
    "dropId": "int",
    "classId": "int",
    "student": "string"
  }
  ```
- **Response**:
  - Success: `200 OK`
    ```json
    { "message": "Request removed" }
    ```
  - Failure: `400 Bad Request` or `500 Internal Server Error`

#### 8. **Create New User**
- **Endpoint**: `/createUser`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "username": "string",
    "newUsername": "string",
    "full_name": "string",
    "newPassword": "string",
    "role": "string"
  }
  ```
- **Response**:
  - Success: `200 OK`
    ```json
    { "message": "User created successfully" }
    ```
  - Failure: `400 Bad Request` or `500 Internal Server Error`

#### 9. **Delete User**
- **Endpoint**: `/deleteuser`
- **Method**: `DELETE`
- **Request Body**:
  ```json
  {
    "adminUsername": "string",
    "username": "string"
  }
  ```
- **Response**:
  - Success: `200 OK`
    ```json
    { "message": "User deleted successfully" }
    ```
  - Failure: `400 Bad Request` or `500 Internal Server Error`

---

### Teacher Endpoints
#### 10. **Get All Classes for a Teacher**
- **Endpoint**: `/getAllClassesTeacher`
- **Method**: `GET`
- **Query Parameters**:
  - `username`: Teacher's username
- **Response**:
  - Success: `200 OK`
    ```json
    {
      "Classes": [
        { "className": "string", "period": "int" }
      ]
    }
    ```
  - Failure: `400 Bad Request` or `500 Internal Server Error`

#### 11. **Get Students in a Class**
- **Endpoint**: `/getStudentsInClass`
- **Method**: `GET`
- **Query Parameters**:
  - `username`: Teacher's username
  - `id`: Class ID
- **Response**:
  - Success: `200 OK`
    ```json
    { "students": ["string"] }
    ```
  - Failure: `400 Bad Request` or `500 Internal Server Error`

---

### Student Endpoints
#### 12. **View Available Classes**
- **Endpoint**: `/studentGetAvailableClasses`
- **Method**: `GET`
- **Query Parameters**:
  - `username`: Student's username
- **Response**:
  - Success: `200 OK`
    ```json
    {
      "result": [
        { "Class Name": "string", "Class Description": "string", "Teacher": "string" }
      ]
    }
    ```
  - Failure: `400 Bad Request` or `500 Internal Server Error`

#### 13. **View Class Info**
- **Endpoint**: `/studentClassInfo`
- **Method**: `GET`
- **Query Parameters**:
  - `username`: Student's username
  - `classId`: Class ID
- **Response**:
  - Success: `200 OK`
    ```json
    {
      "Data": {
        "Class Name": "string",
        "Class Description": "string",
        "Teacher": "string"
      }
    }
    ```
  - Failure: `400 Bad Request` or `500 Internal Server Error`

#### 14. **Submit Drop Request**
- **Endpoint**: `/sendDropRequest`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "username": "string",
    "classId": "int"
  }
  ```
- **Response**:
  - Success: `200 OK`
    ```json
    { "message": "Drop request submitted" }
    ```
  - Failure: `400 Bad Request` or `500 Internal Server Error`

#### 15. **Submit Add Request**
- **Endpoint**: `/sendAddRequest`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "username": "string",
    "classId": "int"
  }
  ```
- **Response**:
  - Success: `200 OK`
    ```json
    { "message": "Add request submitted" }
    ```
  - Failure: `400 Bad Request` or `500 Internal Server Error`

---

### Password Management
#### 16. **Change Password**
- **Endpoint**: `/changePassword`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "username": "string",
    "oldPassword": "string",
    "newPassword": "string"
  }
  ```
- **Response**:
  - Success: `200 OK`
    ```json
    { "message": "Password changed successfully" }
    ```
  - Failure: `400 Bad Request` or `500 Internal Server Error`

---

## Notes
- Ensure database connectivity for all operations.
- Proper role-based checks are enforced in each endpoint.
- All sensitive operations use transaction management and logging for troubleshooting.

---

