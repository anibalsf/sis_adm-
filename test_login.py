import requests
import json

# URL del backend
url = "http://127.0.0.1:8000/api/auth/login"

# Credenciales
data = {
    "username": "admin123",
    "password": "admin123"
}

print("PROBANDO LOGIN AL BACKEND")
print("URL:", url)
print("Datos:", json.dumps(data, indent=2))

try:
    # Hacer la petición POST
    response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
    
    print("\nStatus Code:", response.status_code)
    print("\nRespuesta:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        print("\nLOGIN EXITOSO!")
        token = response.json().get('token')
        print("Token:", token[:20] + "..." if token else "No token")
    else:
        print("\nLOGIN FALLIDO!")
        
except Exception as e:
    print("\nERROR:")
    print(str(e))
