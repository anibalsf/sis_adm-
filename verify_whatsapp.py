import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from comunicacion.services import WhatsAppService
from comunicacion.models import Notificacion

def verify():
    print("Initializing WhatsApp Service...")
    service = WhatsAppService()
    
    if not service.client:
        print("Service initialized (Client is None due to missing credentials, as expected for now).")
    else:
        print("Service initialized with Client.")
        
    print("Attempting to send test message...")
    success, response = service.send_message('70000000', 'Test message from system')
    
    print(f"Send result: Success={success}, Response={response}")
    
    # Check DB
    last_notif = Notificacion.objects.last()
    if last_notif:
        print(f"DB Log found: {last_notif}")
        print(f"Status: {last_notif.estado}")
        print(f"Response Body: {last_notif.response_body}")
    else:
        print("No log found in DB!")

if __name__ == '__main__':
    verify()
