import requests
import sys

# Ensure this matches the running port
AUTH_SERVICE_URL = "http://localhost:8002"

def test_refresh_flow():
    print("--- Testing Refresh Token Flow ---")
    
    # 1. Login to get tokens
    print("\n1. Logging in...")
    login_url = f"{AUTH_SERVICE_URL}/token"
    # Ensure this user exists. If not, register it first or use a known user.
    # Assuming 'testuser' exists from previous steps or we can register a new one.
    username = "refresh_test_user"
    password = "password123"
    
    # Register first to be sure
    register_url = f"{AUTH_SERVICE_URL}/register"
    try:
        requests.post(register_url, json={"username": username, "password": password, "role": "user"})
    except:
        pass # Ignore if already exists

    response = requests.post(login_url, data={"username": username, "password": password})
    
    if response.status_code != 200:
        print(f"Login failed: {response.status_code} {response.text}")
        sys.exit(1)
        
    tokens = response.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    
    print("Login successful.")
    print(f"Access Token: {access_token[:20]}...")
    print(f"Refresh Token: {refresh_token[:20]}...")
    
    if not refresh_token:
        print("Error: No refresh token received.")
        sys.exit(1)

    # 2. Verify Access Token
    print("\n2. Verifying Access Token...")
    verify_url = f"{AUTH_SERVICE_URL}/users/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(verify_url, headers=headers)
    
    if response.status_code == 200:
        print("Access token is valid.")
    else:
        print(f"Access token invalid: {response.status_code}")
        sys.exit(1)

    # 3. Use Refresh Token to get new Access Token
    print("\n3. Refreshing Token...")
    refresh_url = f"{AUTH_SERVICE_URL}/refresh"
    # The endpoint expects the refresh token in the Authorization header as a Bearer token
    # based on: refresh_token: str = Depends(auth.oauth2_scheme)
    headers = {"Authorization": f"Bearer {refresh_token}"}
    
    response = requests.post(refresh_url, headers=headers)
    
    if response.status_code == 200:
        new_tokens = response.json()
        new_access_token = new_tokens.get("access_token")
        new_refresh_token = new_tokens.get("refresh_token")
        print("Refresh successful.")
        print(f"New Access Token: {new_access_token[:20]}...")
        print(f"New Refresh Token: {new_refresh_token[:20]}...")
    else:
        print(f"Refresh failed: {response.status_code} {response.text}")
        sys.exit(1)
        
    # 4. Verify New Access Token
    print("\n4. Verifying New Access Token...")
    headers = {"Authorization": f"Bearer {new_access_token}"}
    response = requests.get(verify_url, headers=headers)
    
    if response.status_code == 200:
        print("New access token is valid.")
    else:
        print(f"New access token invalid: {response.status_code}")
        sys.exit(1)

if __name__ == "__main__":
    test_refresh_flow()
