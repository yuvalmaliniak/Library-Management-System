# Library Management System

### Welcome to the Library Management System! 

This project leverages Docker and NGINX to create a microservices architecture for managing books and loans within a library. 
The repository includes a docker-compose-reverse.yaml file to set up the environment quickly.

## Overview

#### This system is composed of several microservices:



**Books** Service: Manages book information and ratings.

**Loans** Service: Manages loans of books.

**MongoDB**: Database for storing books, ratings, and loans.

**NGINX**: Reverse proxy to route requests to appropriate services.


## Setup
#### The following command will spin up all the containers defined in the docker-compose-reverse.yaml file.
docker-compose -f docker-compose-reverse.yaml up




## Services and Endpoints
### Books Service
Base URL: http://localhost:5001

Endpoints:
#### GET /books: Retrieve all books.
#### GET /books/{id}: Retrieve a specific book by ID.
#### GET /ratings: Retrieve ratings.
#### POST /ratings/{id}/values: Add a rating.

### Loans Service
Base URL: http://localhost:5002

Endpoints:
#### GET /loans: Retrieve all loans.


### NGINX Reverse Proxy
Base URL: http://localhost:80

#### Routes:


Requests to /books, /ratings, and /top are routed to the Books Service.
Requests to /loans are routed to the Loans Service.
Only GET requests are allowed for /books, /ratings, and /loans.
Only POST requests are allowed for /ratings/{id}/values.


## Database
#### MongoDB - Host Port: 27017
#### Contains collections books, ratings, and loans.


Loans Container: Contains the loans service and related configurations.


MongoDB Container: Contains the MongoDB instance.


NGINX Container: Contains the NGINX reverse proxy configurations.



**Optional**: Add summary for each book using Gemini API, contact me for additional info regarding the setup. 
