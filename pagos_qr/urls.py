from rest_framework.routers import DefaultRouter
from .views import QRTransactionViewSet

router = DefaultRouter()
router.register(r'transactions', QRTransactionViewSet, basename='qr-transaction')

urlpatterns = router.urls
