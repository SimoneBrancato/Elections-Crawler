CREATE DATABASE IF NOT EXISTS Elections;
USE Elections;

CREATE TABLE IF NOT EXISTS Trump (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME,
    content VARCHAR(1000) NOT NULL,
    UNIQUE (content(100))
);

CREATE TABLE IF NOT EXISTS Harris (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME,
    content VARCHAR(1000) NOT NULL,
    UNIQUE (content(100))
);