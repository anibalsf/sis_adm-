"""
Script de prueba para verificar las tareas de Celery
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from reportes_auto.tasks import send_daily_report_task, send_weekly_report_task, send_monthly_report_task
from whatsapp_notif.tasks import send_shift_reminders, send_meeting_reminders, send_debt_reminders

def test_celery_tasks():
    """
    Prueba las tareas de Celery
    """
    print("=" * 60)
    print("PRUEBA DE TAREAS DE CELERY")
    print("=" * 60)
    
    print("\n1. Probando reporte diario...")
    try:
        result = send_daily_report_task.delay()
        print(f"   ✅ Tarea enviada: {result.id}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n2. Probando reporte semanal...")
    try:
        result = send_weekly_report_task.delay()
        print(f"   ✅ Tarea enviada: {result.id}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n3. Probando reporte mensual...")
    try:
        result = send_monthly_report_task.delay()
        print(f"   ✅ Tarea enviada: {result.id}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n4. Probando recordatorios de turno...")
    try:
        result = send_shift_reminders.delay()
        print(f"   ✅ Tarea enviada: {result.id}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n5. Probando recordatorios de reunión...")
    try:
        result = send_meeting_reminders.delay()
        print(f"   ✅ Tarea enviada: {result.id}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n6. Probando recordatorios de deuda...")
    try:
        result = send_debt_reminders.delay()
        print(f"   ✅ Tarea enviada: {result.id}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("NOTA: Las tareas se han enviado a Celery.")
    print("Revisa los logs del worker para ver los resultados.")
    print("=" * 60)

if __name__ == '__main__':
    test_celery_tasks()
