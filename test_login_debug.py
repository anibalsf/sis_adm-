import os
import django
import requests

# We cannot easily run django test client without setting up the whole environment, 
# so we will use requests to hit the running server if it's up, OR use Django test client if we setup.
# Let's use Django Test Client as it's safer within this environment without assuming port 8000 is live/accessible to this script.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth.models import User

def test_login():
    client = APIClient()
    
    # Ensure a user exists
    username = 'admin_test_login'
    password = 'password123'
    if not User.objects.filter(username=username).exists():
        User.objects.create_user(username=username, password=password)
        print(f"Created user {username}")

    print(f"Attempting login for {username}...")
    
    # Payload WITHOUT captcha, simulating the new frontend
    data = {
        'username': username,
        'password': password,
        'remember': True
    }
    
    try:
        response = client.post('/api/auth/login', data, format='json')
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.data}")
        
        if response.status_code == 200:
            print("Login SUCCESS!")
        else:
            print("Login FAILED.")
            
    except Exception as e:
        print(f"Exception during request: {e}")

if __name__ == '__main__':
    test_login()
