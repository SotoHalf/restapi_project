# Sample API with MongoDB + Authentication
Distributed System Node Registry with OAuth2 authentication and MongoDB Atlas backend. This API allows for user registration, authentication, and secure access to protected endpoints.

## Project Structure

*   **`main.py`**: The entry point of the application. Contains the FastAPI app definition, lifecycle events (startup/shutdown), and all API endpoints (`/register`, `/token`, `/users/me`, `/system/status`).
*   **`auth.py`**: Handles authentication logic, including password hashing (bcrypt), JWT token creation and verification, and the `get_current_user` dependency.
*   **`database.py`**: Manages the connection to MongoDB Atlas using `motor` (AsyncIO driver).
*   **`models.py`**: Defines the data models for database storage (e.g., `UserInDB`).
*   **`schemas.py`**: Defines Pydantic schemas for API request and response validation (e.g., `UserCreate`, `UserResponse`, `Token`).
*   **`requirements.txt`**: Lists all Python dependencies required to run the project.

## Setup & Deployment

Follow these steps to deploy the application.

### 1. Prerequisites

*   Python 3.8 or higher
*   A MongoDB Atlas account (or a local MongoDB instance)

### 2. Installation

1.  **Clone the repository** (or download the source code).

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Configuration

Create a `.env` file in the root directory with the following variables:

```env
MONGO_URL="mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority"
DB_NAME="whatever"
SECRET_KEY="your_super_secret_key_here"
```

*   Replace `<username>`, `<password>`, and `<cluster>` with your MongoDB Atlas credentials.
*   Generate a strong `SECRET_KEY` (e.g., using `openssl rand -hex 32`).

### 4. Running the Application

Start the development server using Uvicorn:

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### 5. API Documentation

Once the app is running, you can access the interactive API documentation at:

*   **Swagger UI**: `http://127.0.0.1:8000/docs`
*   **ReDoc**: `http://127.0.0.1:8000/redoc`

## Usage

1.  **Register**: POST to `/register` with a username and password.
2.  **Login**: POST to `/token` (OAuth2 form) to get an access token.
3.  **Access Protected Routes**: Use the token to access `/users/me` or `/system/status`. The Swagger UI handles the authorization header automatically if you use the "Authorize" button.
