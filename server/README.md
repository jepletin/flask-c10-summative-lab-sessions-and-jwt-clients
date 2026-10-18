# Productivity API — Flask C10 Summative Lab
## 1. Project Overview

The Productivity API is a web application developed using Flask and React. It allows users to register accounts, authenticate themselves, and manage personal notes.

The backend exposes RESTful API endpoints for user registration, login, retrieving the currently authenticated user, and performing CRUD operations on notes.

The application uses SQLite for data persistence, Flask-SQLAlchemy for database operations, Flask-Bcrypt for password hashing, and Flask-JWT-Extended for token-based authentication.

The React frontend provides a user interface through which users can interact with the backend.

The project demonstrates practical knowledge of backend development, database relationships, authentication, authorization, API design, request validation, and frontend-backend communication.

## 2. Project Objectives

The main objectives of this project are to:

- Build a RESTful API using Flask.
- Create database models using SQLAlchemy.
- Implement user registration and login.
- Protect user passwords through secure hashing.
- Generate and validate JSON Web Tokens (JWTs).
- Restrict protected endpoints to authenticated users.
- Implement Create, Read, Update, and Delete (CRUD) operations.
- Associate notes with their respective owners.
- Implement pagination when retrieving notes.
- Return appropriate HTTP status codes and informative error messages.
- Connect a React frontend to a Flask backend.
- Test API endpoints using Postman.

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| Flask | Web framework for building the API |
| Flask-SQLAlchemy | Database models and ORM operations |
| Flask-Migrate | Database schema migrations |
| Flask-Bcrypt | Password hashing and verification |
| Flask-JWT-Extended | JWT generation and authentication |
| SQLite | Relational database |
| React | Frontend user interface |
| JavaScript | Frontend application logic |
| npm | Frontend dependency management |
| Postman | API testing and debugging |
| Git | Version control |
| GitHub | Source code hosting |

### Why these technologies?

**Flask:** Provides a lightweight framework for creating HTTP routes and processing requests.

**SQLAlchemy:** Allows the application to interact with database records through Python objects instead of writing every SQL query manually.

**Bcrypt:** Protects passwords by storing password hashes rather than plaintext passwords.

**JWT:** Allows the server to authenticate requests using signed tokens.

**SQLite:** Provides a simple relational database suitable for local development and learning.

**React:** Allows the user interface to update and respond to user interactions.

**Postman:** Makes it possible to test backend endpoints independently of the frontend.

## 4. Application Architecture

The application follows a client-server architecture.

### Frontend

The React frontend runs at:

http://localhost:4000

It allows users to interact with the application through forms and other interface components.

### Backend

The Flask backend runs at:

http://localhost:5555

It receives HTTP requests, validates input, performs authentication, interacts with the database, and returns JSON responses.

### Database

SQLite stores registered users and their notes.

### General request flow

1. A user interacts with the React frontend.
2. The frontend sends an HTTP request to the Flask API.
3. Flask processes the request.
4. The backend validates the supplied information.
5. SQLAlchemy reads or modifies database records when necessary.
6. Flask returns a JSON response and an HTTP status code.
7. The frontend processes the response and updates the interface.

For protected endpoints, the client must also provide a valid JWT.

## 5. Project Structure

The project is organized into separate frontend and backend directories.

```text
flask-c10-summative-lab-sessions-and-jwt-clients/
│
├── server/
│   ├── app.py
│   ├── models.py
│   ├── seed.py
│   └── migrations/
│
├── client-with-jwt/
│   ├── public/
│   ├── src/
│   │   └── components/
│   └── package.json
│
└── README.md
```

The exact structure may contain additional files, such as dependency files, configuration files, tests, and stylesheets.

### Backend files

**`app.py`**

Defines the Flask application, configuration, API endpoints, authentication logic, and note management operations.

**`models.py`**

Defines the User and Note database models and their relationship.

**`seed.py`**

Initializes the database and creates sample users and notes.

**`migrations/`**

Contains database migration files generated through Flask-Migrate.

### Frontend files

**`client-with-jwt/`**

Contains the React application.

**`src/components/`**

Contains React components responsible for displaying and handling application functionality.

**`package.json`**

Defines frontend dependencies and available npm scripts.

## 6. Application Features

### 6.1 User Registration

New users can create an account by providing a username, password, and password confirmation.

The registration process:

1. Receives the registration data.
2. Checks that the required fields are provided.
3. Verifies that the password and confirmation match.
4. Checks whether the username already exists.
5. Hashes the password using Bcrypt.
6. Saves the new user to the database.
7. Generates a JWT.
8. Returns the token and user information.

Passwords are not stored as ordinary readable text.

### 6.2 User Login

Registered users can authenticate by providing their username and password.

The backend retrieves the corresponding user record and checks the submitted password against the stored hash.

If the credentials are valid, the application generates a JWT and returns the authenticated user's information.

If the credentials are invalid, the application returns an error response.

The login endpoint also supports informative messages so that the client can communicate the outcome of a login attempt.

For example:

- Login successful! Welcome, nancy_dev27!
- Login failed! Invalid username or password.
- Please enter your username and password.

The backend returns messages as JSON. The React frontend must display them if they are to appear as visible notifications.

### 6.3 Retrieve the Current User

The `/me` endpoint returns information about the currently authenticated user.

It requires a valid JWT.

The endpoint uses the identity contained in the token to locate the corresponding user record.

### 6.4 Create Notes

Authenticated users can create notes by providing a title and content.

Each note is associated with the ID of the authenticated user.

This relationship allows the application to distinguish one user's notes from another user's notes.

### 6.5 Retrieve Notes

Authenticated users can retrieve their personal notes.

The endpoint supports pagination, allowing clients to retrieve notes in smaller groups instead of returning every record in one response.

Pagination parameters include:

- `page`: The requested page number.
- `per_page`: The maximum number of notes requested per page.

The application limits `per_page` to a maximum of 100.

### 6.6 Update Notes

Users can update their own notes through a PATCH request.

The endpoint supports updating the title, content, or both fields.

It rejects empty values for fields supplied in the request.

A user cannot update another user's note through this endpoint because the database query checks both the note ID and the authenticated user's ID.

### 6.7 Delete Notes

Authenticated users can delete their own notes.

The application checks that the requested note belongs to the authenticated user before deleting it.

If the note does not exist or does not belong to that user, the endpoint returns a not-found response.

## 7. Authentication and Authorization

Authentication and authorization are important parts of this application.

### Authentication

Authentication determines whether a user is who they claim to be.

In this project, the login process verifies the username and password.

When the credentials are correct, Flask generates a JSON Web Token.

### Authorization

Authorization determines whether an authenticated user is allowed to access a particular resource.

For example, an authenticated user should be able to manage their own notes but not another user's notes.

### How JWT authentication works

The process follows these steps:

1. The user submits their username and password.
2. Flask retrieves the corresponding user record.
3. Bcrypt verifies the submitted password.
4. Flask generates a signed JWT.
5. The client receives the token.
6. The client includes the token when accessing protected endpoints.
7. Flask validates the token.
8. The application processes the request if authentication succeeds.

### Authorization header

Protected API requests should include the token in the HTTP Authorization header.

```http
Authorization: Bearer <your-jwt-token>
```

In Postman, select:

**Authorization → Bearer Token**

Then paste the token returned by the login endpoint.

### JWT identity

The application creates a token using the user's ID:

```python
token = create_access_token(identity=str(user.id))
```

This allows the backend to identify the user associated with an authenticated request.

The application converts the identity back to an integer when retrieving the user or their notes.

### Important distinction: JWTs and sessions

JWT authentication and session-based authentication are different approaches.

JWT authentication uses a signed token that the client sends with protected requests.

Session-based authentication commonly uses a session identifier stored in a cookie, with session data managed by the server or another configured session store.

This implementation uses Flask-JWT-Extended for authentication. Session-based authentication should only be documented as implemented if the project contains the corresponding session logic.

## 8. Database Design

The application uses SQLite as its relational database.

Two principal models are defined: User and Note.

### 8.1 User model

The User model represents a registered account.

| Field | Description |
|---|---|
| `id` | Unique user identifier |
| `username` | Unique username |
| `password_hash` | Hashed password |

The username is unique, preventing multiple users from registering with the same username.

The password hash is stored instead of the original password.

### 8.2 Note model

The Note model represents a personal note.

| Field | Description |
|---|---|
| `id` | Unique note identifier |
| `title` | Note title |
| `content` | Note content |
| `created_at` | Date and time the note was created |
| `user_id` | ID of the user who owns the note |

The `user_id` field is a foreign key referencing the User table.

### 8.3 Relationship between users and notes

The application implements a one-to-many relationship:

- One user can have many notes.
- Each note belongs to one user.

The relationship is defined using SQLAlchemy:

```python
notes = db.relationship(
    "Note",
    back_populates="user",
    cascade="all, delete-orphan"
)
```

The corresponding relationship in the Note model is:

```python
user = db.relationship(
    "User",
    back_populates="notes"
)
```

The foreign key is defined as:

```python
user_id = db.Column(
    db.Integer,
    db.ForeignKey("users.id"),
    nullable=False
)
```

These definitions connect users to their notes.

## 9. API Documentation

The API communicates using HTTP requests and JSON responses.

### Base URL

```text
http://localhost:5555
```

### 9.1 Root endpoint

**Method:** GET

**Endpoint:** `/`

**Purpose:** Confirms that the API is running.

Example response:

```json
{
  "message": "Productivity API is running!"
}
```

### 9.2 Register a user

**Method:** POST

**Endpoint:** `/signup`

**Purpose:** Creates a new account.

Example request:

```json
{
  "username": "nancy_dev27",
  "password": "NancyPass123!",
  "password_confirmation": "NancyPass123!"
}
```

Successful registration returns HTTP `201 Created`, together with a token and user information.

Possible errors include missing fields, mismatched passwords, and duplicate usernames.

### 9.3 Log in

**Method:** POST

**Endpoint:** `/login`

**Purpose:** Authenticates an existing user.

Example request:

```json
{
  "username": "nancy_dev27",
  "password": "NancyPass123!"
}
```

A successful request returns HTTP `200 OK`.

An unsuccessful login returns HTTP `401 Unauthorized`.

The exact response fields depend on the current implementation of the login route.

### 9.4 Retrieve the current user

**Method:** GET

**Endpoint:** `/me`

**Purpose:** Retrieves the authenticated user's details.

**Authentication:** Required.

Example successful response:

```json
{
  "id": 3,
  "username": "nancy_dev27"
}
```

The ID is illustrative.

### 9.5 Create a note

**Method:** POST

**Endpoint:** `/notes`

**Purpose:** Creates a note for the authenticated user.

**Authentication:** Required.

Example request:

```json
{
  "title": "Learn Flask",
  "content": "Practise Flask authentication and API routes."
}
```

A successful request returns HTTP `201 Created`.

### 9.6 Retrieve notes

**Method:** GET

**Endpoint:** `/notes`

**Purpose:** Retrieves the authenticated user's notes.

**Authentication:** Required.

Example request:

```text
GET /notes?page=1&per_page=10
```

Example response structure:

```json
{
  "notes": [],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total_notes": 0,
    "total_pages": 0,
    "has_next": false,
    "has_previous": false
  }
}
```

The empty notes array is an example of the response structure, not a claim about the current database contents.

### 9.7 Update a note

**Method:** PATCH

**Endpoint:** `/notes/<note_id>`

**Purpose:** Updates an existing note belonging to the authenticated user.

**Authentication:** Required.

Example request:

```json
{
  "title": "Learn Flask and JWT"
}
```

Replace `<note_id>` with the ID of the note to update.

A successful request returns HTTP `200 OK`.

### 9.8 Delete a note

**Method:** DELETE

**Endpoint:** `/notes/<note_id>`

**Purpose:** Deletes a note belonging to the authenticated user.

**Authentication:** Required.

Example:

```text
DELETE /notes/1
```

Replace `1` with the ID of the note to delete.

A successful request returns a confirmation message.

### Endpoint summary

| Method | Endpoint | Authentication | Purpose |
|---|---|---|---|
| GET | `/` | No | Check API status |
| POST | `/signup` | No | Register a user |
| POST | `/login` | No | Authenticate a user |
| GET | `/me` | Yes | Retrieve current user |
| POST | `/notes` | Yes | Create a note |
| GET | `/notes` | Yes | Retrieve personal notes |
| PATCH | `/notes/<note_id>` | Yes | Update a note |
| DELETE | `/notes/<note_id>` | Yes | Delete a note |

## 10. Installation and Setup

### Prerequisites

Install the following software:

- Python 3
- Node.js and npm
- Git
- Postman (optional, for API testing)

### Step 1: Clone the repository

```bash
git clone <your-repository-url>
```

Navigate to the project directory:

```bash
cd flask-c10-summative-lab-sessions-and-jwt-clients
```

Replace `<your-repository-url>` with the actual repository URL.

### Step 2: Set up the backend environment

Navigate to the server directory:

```bash
cd server
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it on Ubuntu:

```bash
source .venv/bin/activate
```

Install the project's backend dependencies using its dependency file.

If the project contains a `requirements.txt` file, run:

```bash
pip install -r requirements.txt
```

If the project uses Pipenv, follow the instructions in its Pipfile instead.

### Step 3: Initialize the database

The project uses SQLite.

If the database has not yet been initialized, the supplied seed script can create the tables and sample data:

```bash
python seed.py
```

The seed script creates sample users and notes if they do not already exist.

It does not automatically reset an existing user's password.

### Step 4: Start the Flask backend

From the `server` directory, run:

```bash
python app.py
```

The backend should be available at:

```text
http://localhost:5555
```

### Step 5: Install frontend dependencies

Open a second terminal:

```bash
cd ~/flask-c10-summative-lab-sessions-and-jwt-clients/client-with-jwt
```

Install the frontend dependencies:

```bash
npm install
```

### Step 6: Start the React frontend

Use the start command configured in the frontend's `package.json`.

If the project provides a `start` script, run:

```bash
npm start
```

Open the application in your browser:

```text
http://localhost:4000
```

Keep both the backend and frontend running while using the application.

## 11. Running the Application

The application requires two running processes during local development.

### Terminal 1: Flask backend

```bash
cd ~/flask-c10-summative-lab-sessions-and-jwt-clients/server
source .venv/bin/activate
python app.py
```

### Terminal 2: React frontend

```bash
cd ~/flask-c10-summative-lab-sessions-and-jwt-clients/client-with-jwt
npm start
```

The backend handles API requests, while the frontend displays the application.

If the frontend cannot connect to Flask, check that the backend is running on port `5555` and that the frontend proxy configuration points to the correct port.

## 12. Testing with Postman

Postman can be used to test the API without relying on the React interface.

### Test 1: Check the API

Send:

```http
GET http://localhost:5555/
```

Confirm that the API returns its status message.

### Test 2: Register a new user

Send:

```http
POST http://localhost:5555/signup
```

Set the body to raw JSON:

```json
{
  "username": "nancy_dev27",
  "password": "NancyPass123!",
  "password_confirmation": "NancyPass123!"
}
```

Confirm that the request succeeds and returns a token.

If the username already exists, use another username or log in to the existing account.

### Test 3: Log in

Send:

```http
POST http://localhost:5555/login
```

Use:

```json
{
  "username": "nancy_dev27",
  "password": "NancyPass123!"
}
```

Confirm that the response indicates successful authentication.

### Test 4: Retrieve the current user

Send:

```http
GET http://localhost:5555/me
```

Select **Authorization → Bearer Token** and enter the JWT returned by login.

Confirm that the response contains the authenticated user's details.

### Test 5: Create a note

Send:

```http
POST http://localhost:5555/notes
```

Include the JWT in the Authorization header.

Body:

```json
{
  "title": "My first note",
  "content": "Testing the Productivity API."
}
```

Confirm that the response contains the new note.

### Test 6: Retrieve notes

Send:

```http
GET http://localhost:5555/notes
```

Include the JWT.

Confirm that the response contains the authenticated user's notes and pagination information.

### Test 7: Update a note

Send a PATCH request to the note's URL:

```http
PATCH http://localhost:5555/notes/1
```

Replace `1` with the actual note ID.

Example body:

```json
{
  "title": "Updated note"
}
```

Confirm that the title changes.

### Test 8: Delete a note

Send:

```http
DELETE http://localhost:5555/notes/1
```

Replace `1` with the actual note ID.

Include the JWT and confirm that the API reports successful deletion.

## 13. Error Handling

The API uses HTTP status codes to communicate the outcome of requests.

| Status code | Meaning | Example |
|---|---|---|
| `200 OK` | Request succeeded | Successful login or note retrieval |
| `201 Created` | Resource created | Successful signup or note creation |
| `400 Bad Request` | Invalid input | Missing fields or invalid pagination |
| `401 Unauthorized` | Authentication failed or is required | Invalid credentials or missing/invalid JWT |
| `404 Not Found` | Resource not found | Note or user does not exist |
| `409 Conflict` | Resource conflicts with existing data | Username already exists |

The precise response depends on the route and the type of error.

The application validates input to prevent incomplete or invalid data from being processed.

For login, the API can return a JSON message explaining that the credentials are invalid.

For note operations, it returns errors when required fields are missing, pagination values are invalid, or the requested note cannot be found.

## 14. Security Considerations

### Password hashing

Passwords should never be stored as plaintext.

The application uses Bcrypt to generate password hashes and verify submitted passwords.

### JWT protection

Protected endpoints use JWT validation to ensure that requests include valid authentication credentials.

### Resource ownership

The note update and delete operations check both the note ID and the authenticated user's ID.

This prevents users from modifying or deleting notes belonging to other users through those routes.

### Secret key management

The development configuration currently contains a JWT secret key.

For production, the secret should be loaded from an environment variable and excluded from version control.

### Input validation

The application checks required fields and rejects invalid values before creating or updating database records.

### Development versus production

The application is configured for local development.

Before deployment, review the secret-key configuration, debugging settings, database configuration, HTTPS requirements, and error handling.

## 15. Challenges and Solutions

The project provides opportunities to practise debugging common backend development problems.

### Challenge 1: Authentication failures

A login request can fail when the username does not exist or the password does not match the stored hash.

**Solution:** Verify that the account exists, use the correct password, and ensure that passwords are checked using Bcrypt.

### Challenge 2: JWT authentication

Protected endpoints reject requests without a valid token.

**Solution:** Obtain a token through successful login and include it in the Authorization header.

### Challenge 3: Frontend-backend communication

The React frontend and Flask backend run on different ports.

If the frontend proxy targets a backend that is not running, requests may fail.

**Solution:** Start the backend and verify that the proxy configuration points to the correct port.

### Challenge 4: Duplicate usernames

The database requires usernames to be unique.

Attempting to register an existing username results in a conflict.

**Solution:** Use a new username or log in to the existing account.

### Challenge 5: Database relationships

Each note must be associated with its owner.

**Solution:** Use a foreign key and SQLAlchemy relationships to connect the User and Note models.

## 16. Learning Outcomes

Through this project, I practised the following concepts.

### Backend development

- Creating routes with Flask.
- Processing JSON requests.
- Returning JSON responses.
- Using HTTP methods and status codes.

### Database management

- Defining SQLAlchemy models.
- Creating primary keys and foreign keys.
- Establishing one-to-many relationships.
- Querying database records.
- Performing CRUD operations.
- Using database migrations.

### Authentication and security

- Hashing passwords with Bcrypt.
- Verifying submitted passwords.
- Generating JWTs.
- Protecting API endpoints.
- Identifying authenticated users.
- Restricting access to user-owned resources.

### API development

- Designing RESTful endpoints.
- Validating request data.
- Returning informative error messages.
- Implementing pagination.
- Testing API behavior with Postman.

### Frontend-backend integration

- Sending requests from React to Flask.
- Processing JSON responses.
- Handling login success and failure.
- Connecting frontend authentication flows to backend JWTs.

## 17. Future Improvements

Potential improvements include:

- Adding automated unit and integration tests.
- Improving frontend success and error notifications.
- Adding note search and filtering.
- Supporting note categories and tags.
- Implementing account profile management.
- Adding password reset functionality.
- Improving validation and API documentation.
- Moving secrets into environment variables.
- Adding rate limiting to authentication endpoints.
- Deploying the backend and frontend.
- Introducing session-based authentication if required by the lab.
- Adding CI checks to run tests automatically.

These are possible future improvements, not claims that all these features are already implemented.

## 18. Conclusion

The Productivity API demonstrates the development of a web application using Flask, SQLAlchemy, SQLite, and JWT authentication.

It allows users to register, log in, retrieve their account information, and manage personal notes through protected API endpoints.

The project combines backend development, database management, authentication, authorization, and React integration into a practical learning experience.

It provides a foundation for building more advanced web applications with secure authentication, reliable database operations, and clear API design.