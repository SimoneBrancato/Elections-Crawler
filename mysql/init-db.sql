CREATE DATABASE IF NOT EXISTS Elections;
USE Elections;

CREATE TABLE IF NOT EXISTS Posts (
    uuid CHAR(36) PRIMARY KEY,
    timestamp DATETIME,
    candidate VARCHAR(50) NOT NULL,
    content VARCHAR(1000) NOT NULL,
    `like` INT DEFAULT 0,
    love INT DEFAULT 0,
    care INT DEFAULT 0,
    haha INT DEFAULT 0,
    wow INT DEFAULT 0,
    angry INT DEFAULT 0, 
    sad INT DEFAULT 0, 
    UNIQUE (content(100))
);

CREATE TABLE IF NOT EXISTS Comments (
    uuid CHAR(36) PRIMARY KEY,
    post_id CHAR(36),
    content VARCHAR(1000) NOT NULL,
    UNIQUE (content(100)),
    FOREIGN KEY (post_id) REFERENCES Posts(uuid) ON DELETE CASCADE
);
