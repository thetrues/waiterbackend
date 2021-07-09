from core.models import Item, MeasurementUnit
from core.serializers import (
    ItemSerializer,
    MeasurementUnitSerializer,
)
from rest_framework import permissions
from rest_framework import viewsets
from icecream import ic


class MeasurementUnitViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]
    queryset = MeasurementUnit.objects.all()
    serializer_class = MeasurementUnitSerializer


class ItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
