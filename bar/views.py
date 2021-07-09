from rest_framework import permissions, viewsets
from bar.serializers import (
    RegularInventoryRecordSerializer,
    TekilaInventoryRecordSerializer,
)
from bar.models import RegularInventoryRecord, TekilaInventoryRecord
from rest_framework.authentication import TokenAuthentication


class RegularInventoryRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]
    queryset = RegularInventoryRecord.objects.all()
    serializer_class = RegularInventoryRecordSerializer
    authentication_classes = (TokenAuthentication,)


class TekilaInventoryRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]
    queryset = TekilaInventoryRecord.objects.all()
    serializer_class = TekilaInventoryRecordSerializer
    authentication_classes = (TokenAuthentication,)
