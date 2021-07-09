from rest_framework import permissions, viewsets
from bar.serializers import (
    RegularInventoryRecordSerializer,
    TekilaInventoryRecordSerializer,
)
from bar.models import RegularInventoryRecord, TekilaInventoryRecord


class RegularInventoryRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]
    queryset = RegularInventoryRecord.objects.all()
    serializer_class = RegularInventoryRecordSerializer


class TekilaInventoryRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]
    queryset = TekilaInventoryRecord.objects.all()
    serializer_class = TekilaInventoryRecordSerializer
