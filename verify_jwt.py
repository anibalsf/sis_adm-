import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/auth"

def test_jwt_flow():
    print("=== TEST JWT AUTHENTICATION FLOW ===")
    
    # 1. Login
    login_url = f"{BASE_URL}/login"
    payload = {"username": "admin123", "password": "admin123"}
    print(f"\n1. Intentando login en {login_url}...")
    
    try:
        res = requests.post(login_url, json=payload)
        if res.status_code != 200:
            print(f"❌ Error en login: {res.status_code}")
            print(res.text)
            return
        
        data = res.json()
        access_token = data.get('access')
        refresh_token = data.get('refresh')
        
        if not access_token or not refresh_token:
            print("❌ No se recibieron los tokens JWT esperados.")
            print(json.dumps(data, indent=2))
            return
            
        print("✅ Login exitoso. Tokens recibidos.")
        print(f"Access (truncado): {access_token[:20]}...")
        print(f"Refresh (truncado): {refresh_token[:20]}...")

        # 2. Test Access Token (Me)
        me_url = f"{BASE_URL}/me"
        print(f"\n2. Probando access token en {me_url}...")
        res_me = requests.get(me_url, headers={"Authorization": f"Bearer {access_token}"})
        
        if res_me.status_code == 200:
            print("✅ Access token funciona correctamente.")
            print(f"Usuario: {res_me.json().get('username')}")
        else:
            print(f"❌ Error validando access token: {res_me.status_code}")
            return

        # 3. Test Token Refresh
        refresh_url = f"{BASE_URL}/token/refresh/"
        print(f"\n3. Probando refresco de token en {refresh_url}...")
        res_ref = requests.post(refresh_url, json={"refresh": refresh_token})
        
        if res_ref.status_code == 200:
            new_access = res_ref.json().get('access')
            print("✅ Token refrescado exitosamente.")
            print(f"Nuevo Access (truncado): {new_access[:20]}...")
        else:
            print(f"❌ Error al refrescar token: {res_ref.status_code}")
            print(res_ref.text)
            return

        # 4. Test Logout (Blacklist)
        logout_url = f"{BASE_URL}/logout"
        print(f"\n4. Probando logout (blacklist) en {logout_url}...")
        res_out = requests.post(logout_url, json={"refresh": refresh_token}, headers={"Authorization": f"Bearer {access_token}"})
        
        if res_out.status_code == 200:
            print("✅ Logout exitoso.")
        else:
            print(f"❌ Error en logout: {res_out.status_code}")

    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")

if __name__ == "__main__":
    test_jwt_flow()
