import os
import sys
import requests
import logging
from logging_config import setup_logging
from datetime import timedelta

# Mock environment variables
os.environ["SECRET_KEY"] = "test_secret"

# Add current directory to path so we can import auth
sys.path.append(os.getcwd())

try:
    import auth
    print("Successfully imported auth")
except Exception as e:
    print(f"Failed to import auth: {e}")
    sys.exit(1)

def verify_token(token):
    setup_logging()
    logger = logging.getLogger(__name__)
    # AUTH_SERVICE_URL is not defined in the original code, assuming it's a placeholder
    # For this example, we'll mock it or assume it's defined elsewhere.
    # If it's meant to be a test, it might not actually call an external service.
    # Let's assume for now it's a placeholder for a real service URL.
    # For a functional example, you'd need to define AUTH_SERVICE_URL.
    AUTH_SERVICE_URL = "http://localhost:8002" # Placeholder
    url = f"{AUTH_SERVICE_URL}/users/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        logger.info(f"Verifying token with {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        logger.info(f"Token verification successful: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Token verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during token verification: {e}")
        return None

def test_create_access_token():
    data = {"sub": "testuser"}
    
    # Test with default expiration
    try:
        token = auth.create_access_token(data)
        print("Successfully created token with default expiration")
    except Exception as e:
        print(f"Failed to create token with default expiration: {e}")
        sys.exit(1)

    # Test with custom expiration
    try:
        expires = timedelta(minutes=30)
        token = auth.create_access_token(data, expires_delta=expires)
        print("Successfully created token with custom expiration")
    except Exception as e:
        print(f"Failed to create token with custom expiration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_create_access_token()
    
    # Create a token and verify it
    print("\n--- Verifying Token against API ---")
    data = {"sub": "testuser"} # Make sure this user exists in DB or mock it if auth service doesn't check DB for token validation (it does check DB in get_current_user)
    # Note: 'testuser' might not exist in DB if we haven't registered it.
    # We should probably register a user first or use an existing one.
    # For now let's try with 'testuser' and see if it fails (which generates logs too).
    token = auth.create_access_token(data)
    verify_token(token)
