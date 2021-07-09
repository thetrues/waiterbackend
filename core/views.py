from rest_framework.authentication import TokenAuthentication
from core.models import Item, MeasurementUnit
from core.serializers import (
    ItemSerializer,
    MeasurementUnitSerializer,
)
from rest_framework import permissions
from rest_framework import viewsets
from icecream import ic


class MeasurementUnitViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = MeasurementUnit.objects.all()
    serializer_class = MeasurementUnitSerializer
    authentication_classes = [TokenAuthentication]


class ItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    authentication_classes = [TokenAuthentication]
