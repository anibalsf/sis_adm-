import os
import sys
print("SYS.PATH:", sys.path)

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
try:
    django.setup()
    print("Django Setup SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
