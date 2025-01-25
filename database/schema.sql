-- User Table: Tracks all users (admin, students, and teachers)
CREATE TABLE Users (
    username VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(50) NOT NULL,
    salt BLOB NOT NULL,
    hash BLOB NOT NULL,
    role VARCHAR(50) NOT NULL,
    FOREIGN KEY (role) REFERENCES Roles(role)
);

-- Roles Table: Defines roles (admin, teacher, student)
CREATE TABLE Roles (
    role VARCHAR(50) PRIMARY KEY
);

-- Classes Table: Stores class details
CREATE TABLE Classes (
    id INTEGER PRIMARY KEY,
    className VARCHAR(50) NOT NULL,
    classDescription TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    teacher VARCHAR(50) NOT NULL,
    period INTEGER NOT NULL,
    FOREIGN KEY (teacher) REFERENCES Users(full_name)
);

-- ClassStudents Table (Junction Table): Links students to classes
CREATE TABLE ClassStudents (
    id INTEGER PRIMARY KEY,
    classId INTEGER NOT NULL,
    student VARCHAR(50) NOT NULL,
    FOREIGN KEY (classId) REFERENCES Classes(id),
    FOREIGN KEY (student) REFERENCES Users(full_name)
);

-- Drop Requests Table: Tracks class drop requests
CREATE TABLE DropRequests (
    id INTEGER PRIMARY KEY,
    classId INTEGER NOT NULL,
    student VARCHAR(50) NOT NULL,
    FOREIGN KEY (classId) REFERENCES Classes(id),
    FOREIGN KEY (student) REFERENCES Users(full_name)
);

-- Add Requests Table: Tracks class add requests
CREATE TABLE AddRequests (
    id INTEGER PRIMARY KEY,
    classId INTEGER NOT NULL,
    student VARCHAR(50) NOT NULL,
    FOREIGN KEY (classId) REFERENCES Classes(id),
    FOREIGN KEY (student) REFERENCES Users(full_name)
);

-- Student Schedule Table: Tracks students' schedules (redundant with ClassStudents)
CREATE TABLE StudentSchedule (
    id INTEGER PRIMARY KEY,
    student VARCHAR(50) NOT NULL,
    classId INTEGER NOT NULL,
    period INTEGER NOT NULL,
    FOREIGN KEY (student) REFERENCES Users(full_name),
    FOREIGN KEY (classId) REFERENCES Classes(id)
);

-- Teacher Schedule Table: Tracks teachers' schedules
CREATE TABLE TeacherSchedule (
    id INTEGER PRIMARY KEY,
    teacher VARCHAR(50) NOT NULL,
    classId INTEGER NOT NULL,
    FOREIGN KEY (teacher) REFERENCES Users(full_name),
    FOREIGN KEY (classId) REFERENCES Classes(id)
);