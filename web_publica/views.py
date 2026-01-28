from rest_framework import viewsets, permissions
from .models import Multimedia
from .serializers import MultimediaSerializer

class MultimediaViewSet(viewsets.ModelViewSet):
    queryset = Multimedia.objects.filter(activo=True)
    serializer_class = MultimediaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
