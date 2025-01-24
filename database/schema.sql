CREATE TABLE Users (
    username VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(50) NOT NULL,
    salt BLOB NOT NULL,
    hash BLOB NOT NULL,
    role VARCHAR(50) NOT NULL,
    FOREIGN KEY (role) REFERENCES Roles(role)
);

CREATE TABLE Roles (
    role VARCHAR(50) PRIMARY KEY
);

CREATE TABLE Classes (
    id INTEGER PRIMARY KEY,
    className VARCHAR(50) NOT NULL,
    classDescription TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    teacher VARCHAR(50) NOT NULL,
    student VARCHAR(50),
    period INTEGER NOT NULL,
    FOREIGN KEY (teacher) REFERENCES Users(full_name),
    FOREIGN KEY (student) REFERENCES Users(full_name)
);

CREATE TABLE dropClasses (
    id INTEGER PRIMARY KEY,
    classId VARCHAR(50) NOT NULL,
    student VARCHAR(50) NOT NULL,
    FOREIGN KEY (classId) REFERENCES Classes (id),
    FOREIGN KEY (student) REFERENCES Classes (student)
);

CREATE TABLE addClasses (
    id INTEGER PRIMARY KEY,
    classId VARCHAR(50) NOT NULL,
    student VARCHAR(50) NOT NULL,
    FOREIGN KEY (classId) REFERENCES Classes (id),
    FOREIGN KEY (student) REFERENCES Classes (student)
);

CREATE TABLE StudentSchedule (
    id INTEGER PRIMARY KEY,
    student VARCHAR(50) NOT NULL,
    classId INTEGER NOT NULL,
    period INTEGER NOT NULL,
    FOREIGN KEY (student) REFERENCES Users(full_name),
    FOREIGN KEY (classId) REFERENCES Classes(id)
);

CREATE TABLE TeacherSchedule (
    id INTEGER PRIMARY KEY,
    teacher VARCHAR(50) NOT NULL,
    classId INTEGER NOT NULL,
    FOREIGN KEY (teacher) REFERENCES Users(full_name),
    FOREIGN KEY (classId) REFERENCES Classes(id)
);