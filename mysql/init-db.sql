CREATE DATABASE IF NOT EXISTS Elections;
USE Elections;

CREATE TABLE IF NOT EXISTS Posts (
    uuid CHAR(100),
    retrieving_time DATETIME,
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
    PRIMARY KEY (uuid, retrieving_time)
);

CREATE TABLE IF NOT EXISTS Comments (
    uuid CHAR(100),
    post_id CHAR(100),
    retrieving_time DATETIME,
    timestamp DATETIME,
    account CHAR(36),
    content VARCHAR(1000) NOT NULL,
    `like` INT DEFAULT 0,
    love INT DEFAULT 0,
    care INT DEFAULT 0,
    haha INT DEFAULT 0,
    wow INT DEFAULT 0,
    angry INT DEFAULT 0, 
    sad INT DEFAULT 0, 
    PRIMARY KEY (uuid, retrieving_time),
    FOREIGN KEY (post_id) REFERENCES Posts(uuid) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Links (
    timestamp DATETIME,
    candidate VARCHAR(50) NOT NULL,
    post_link VARCHAR(150),
    PRIMARY KEY (post_link)
);