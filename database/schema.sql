CREATE TABLE Users (
    username VARCHAR(50) PRIMARY KEY,
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
    name VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    teacher VARCHAR(50) NOT NULL,
    student VARCHAR(50) NOT NULL,
    FOREIGN KEY (teacher) REFERENCES Users(username),
    FOREIGN KEY (student) REFERENCES Users(username)
);