create database IF not EXISTS all_to_the_bottom;
use all_to_the_bottom;
CREATE TABLE IF not EXISTS Requests(
    requestId VARCHAR(10),
    country VARCHAR(45),
    d DATE,
    t TIME,
    category VARCHAR(45)
);