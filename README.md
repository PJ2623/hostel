# Hostel Management API

<p align="center">
    <img src="assets/dobs.png">
</p>

## Project Inspiration

St Joseph's RC High School is a high school that houses all its learners in hostels.
One for the boys and another for the girls. As a former learner at this amazing school
I designed this API with my experience in the boy's hostel in mind.<br><br>There are
two main actors in the hostel, mainly learners and supervisors or matrons, of which there
are two, one for senior learners (grades 10 - 12) and another for junior learners (grades 9 - 8).
Each grade has their own **block** or dorm, with grades 11 and 12, sharing the same **block**.

---

This is a FastAPI-based backend API designed for managing staff and learners in a hostel environment. The API facilitates managing learner and staff data, including adding, retrieving, updating, and deleting learner and staff profiles, attendance tracking, and more. The system is designed to handle access control based on roles, such as junior matrons, senior matrons, and chief matrons.

## Features

- **Learner Management**  
  - Add new learners to the database.
  - Fetch learner details and images.
  - View all learners for a specific matron.
  - Enforce block access restrictions based on the matron's role.

- **Staff Management**  
  - Add new staff members with role-based permissions.
  - Fetch staff details and images.
  - Delete staff accounts with access control.

- **Role-Based Access Control**  
  - Junior matrons, senior matrons, and chief matrons can have different levels of access.
  - Specific roles can access or modify only certain resources, such as learners in specific blocks or staff accounts.

---

## Endpoints

### Learner Endpoints

#### `POST /api/v1/learner`
- **Description**: Adds a new learner to the database.
- **Request Body**:
  - `profile`: The learner's profile picture (image).
  - `first_name`: First name of the learner.
  - `last_name`: Last name of the learner.
  - `block`: The block the learner is assigned to.
  - `room`: The room the learner is assigned to.
  - `grade`: The grade the learner is in.
- **Response**: 
  - A JSON object with the learner's ID and a success message.
  
#### `GET /api/v1/learner/{id}`
- **Description**: Fetches details of a specific learner by ID.
- **Response**: Learner's details excluding the image (returns JSON).

#### `GET /api/v1/learner/{id}/image`
- **Description**: Fetches the profile image of a specific learner by ID.
- **Response**: The image in JPEG format.

#### `GET /api/v1/learner`
- **Description**: Fetches all learners that the current matron is authorized to access.
- **Response**: A list of learners.

#### `DELETE /api/v1/learner/{id}`
- **Description**: Deletes a learner from the database.
- **Response**: A success message or an error message if the learner doesn't exist.

---

### Staff Endpoints

#### `POST /api/v1/staff`
- **Description**: Adds a new staff member to the system.
- **Request Body**:
  - `profile`: The staff member's profile picture (image).
  - `first_name`: First name of the staff member.
  - `last_name`: Last name of the staff member.
  - `username`: The username for logging in.
  - `role`: The staff member's role (e.g., junior matron, senior matron, etc.).
  - `password`: The password to be used for login.
  - `verify_password`: Should match `password`.
- **Response**: A success message with the username.

#### `GET /api/v1/staff/{id}`
- **Description**: Fetches details of a specific staff member by their ID.
- **Response**: Staff member's details excluding the image, password, and permissions.

#### `GET /api/v1/staff/{id}/image`
- **Description**: Fetches the profile image of a specific staff member by ID.
- **Response**: The image in JPEG format.

#### `DELETE /api/v1/staff/{id}`
- **Description**: Deletes a staff member's account.
- **Response**: A success message or an error message if the staff member doesn't exist.

---

## Authentication & Authorization

The system uses role-based access control (RBAC) to restrict access to certain endpoints based on the current user's role.

- **Roles**:
  - `chief-matron`: Has the highest level of access.
  - `junior-matron`: Can access and manage learners in certain blocks and perform basic staff management tasks.
  - `senior-matron`: Can access and manage learners in other blocks and perform similar tasks to junior matrons.
  - `super-user`: Has unrestricted access across the platform.

### Access Control

- **Learner Management**: 
  - A junior matron can only add or view learners in blocks C or D.
  - A senior matron can only add or view learners in blocks A or B.
  
- **Staff Management**:
  - A chief matron cannot create or delete a `super-user`.
  - Junior and senior matrons can only view and modify their own accounts.

---

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (e.g., database connection, JWT secret):
   ```bash
   cp .env.example .env
   ```

4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

---

## Technologies Used

- **FastAPI**: Web framework for building APIs.
- **Pydantic**: Data validation and settings management.
- **MongoDB**: Database for storing learner and staff information.
- **JWT (JSON Web Token)**: For user authentication and authorization.
- **Pillow**: For handling image data (profile pictures).

---