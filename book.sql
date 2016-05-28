CREATE TABLE IF NOT EXISTS Books (ID INTEGER PRIMARY KEY,
									ISBN TEXT,
									Title TEXT,
									Author TEXT,
									Pages INT,
									averageRating FLOAT,
									Thumb TEXT,
									userID INT);
									
CREATE TABLE IF NOT EXISTS Users (ID INTEGER PRIMARY KEY,
									loginname TEXT,
									loginpw TEXT);
									